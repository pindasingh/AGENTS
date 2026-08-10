/*
 * Web tools inspired by the public OpenCode websearch/webfetch tool concepts:
 * https://github.com/anomalyco/opencode/tree/dev/packages/opencode/src/tool
 * This is an independent Pi implementation; it does not claim exact OpenCode behavior.
 */

import { lookup } from "node:dns/promises";
import { mkdtemp, writeFile } from "node:fs/promises";
import { request as httpRequest } from "node:http";
import { isIP } from "node:net";
import { request as httpsRequest } from "node:https";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  DEFAULT_MAX_BYTES,
  DEFAULT_MAX_LINES,
  formatSize,
  truncateHead,
  type ExtensionAPI,
  type TruncationResult,
} from "@earendil-works/pi-coding-agent";
import { StringEnum } from "@earendil-works/pi-ai";
import { Text } from "@earendil-works/pi-tui";
import { Type } from "typebox";

const SEARCH_TIMEOUT_MS = 30_000;
const FETCH_DEFAULT_TIMEOUT_SECONDS = 30;
const FETCH_MAX_TIMEOUT_SECONDS = 120;
const FETCH_MAX_BYTES = 5 * 1024 * 1024;
const FETCH_MAX_IMAGE_BYTES = 1024 * 1024;
const FETCH_MAX_REDIRECTS = 5;
const EXA_MCP_URL = "https://mcp.exa.ai/mcp";
const PARALLEL_SEARCH_URL = "https://search.parallel.ai/mcp";
const USER_AGENT = "pi-opencode-inspired-web-tools/1.0";

const WebSearchParams = Type.Object(
  {
    query: Type.String({
      description: "A specific web search query",
      minLength: 1,
      maxLength: 2_000,
    }),
    numResults: Type.Optional(Type.Integer({ description: "Desired result count (default 8)", minimum: 1, maximum: 20 })),
    livecrawl: Type.Optional(StringEnum(["fallback", "preferred"] as const, { description: "Whether live crawling is preferred" })),
    type: Type.Optional(StringEnum(["auto", "fast", "deep"] as const, { description: "Search depth/speed tradeoff" })),
    contextMaxCharacters: Type.Optional(
      Type.Integer({ description: "Maximum result context characters (default 10000)", minimum: 1000, maximum: 50000 }),
    ),
  },
  { additionalProperties: false },
);

const WebFetchParams = Type.Object(
  {
    url: Type.String({ description: "An absolute http or https URL", minLength: 1, maxLength: 16_384 }),
    format: Type.Optional(
      Type.String({
        description: "Output format for HTML: markdown (default), text, or html",
        pattern: "^(markdown|text|html)$",
      }),
    ),
    timeout: Type.Optional(
      Type.Integer({
        description: `Timeout in seconds (default ${FETCH_DEFAULT_TIMEOUT_SECONDS}, maximum ${FETCH_MAX_TIMEOUT_SECONDS})`,
        minimum: 1,
        maximum: FETCH_MAX_TIMEOUT_SECONDS,
      }),
    ),
  },
  { additionalProperties: false },
);

type SearchProvider = "exa" | "parallel";
type FetchFormat = "markdown" | "text" | "html";

interface OutputDetails {
  kind: "search" | "fetch";
  provider?: SearchProvider;
  url?: string;
  contentType?: string;
  bytes?: number;
  truncated?: TruncationResult;
  fullOutputPath?: string;
  image?: boolean;
}

interface JsonRpcEnvelope {
  jsonrpc?: string;
  id?: unknown;
  result?: unknown;
  error?: { code?: unknown; message?: unknown; data?: unknown };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function createRequestSignal(parent: AbortSignal | undefined, timeoutMs: number) {
  const controller = new AbortController();
  let timedOut = false;

  const onParentAbort = () => controller.abort(parent?.reason ?? new Error("Cancelled"));
  if (parent?.aborted) onParentAbort();
  else parent?.addEventListener("abort", onParentAbort, { once: true });

  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort(new Error(`Timed out after ${timeoutMs}ms`));
  }, timeoutMs);
  timer.unref?.();

  return {
    signal: controller.signal,
    timedOut: () => timedOut,
    cleanup: () => {
      clearTimeout(timer);
      parent?.removeEventListener("abort", onParentAbort);
    },
  };
}

async function readResponseBytes(response: Response, maximum: number): Promise<Uint8Array> {
  const declaredLength = Number(response.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > maximum) {
    await response.body?.cancel();
    throw new Error(`response is too large (${formatSize(declaredLength)}; maximum ${formatSize(maximum)})`);
  }

  if (!response.body) return new Uint8Array();
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value) continue;
      size += value.byteLength;
      if (size > maximum) {
        await reader.cancel();
        throw new Error(`response exceeded the ${formatSize(maximum)} maximum`);
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const output = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return output;
}

function decodeBytes(bytes: Uint8Array, contentType: string): string {
  const charset = /charset\s*=\s*["']?([^;"'\s]+)/i.exec(contentType)?.[1] ?? "utf-8";
  try {
    return new TextDecoder(charset).decode(bytes);
  } catch {
    return new TextDecoder("utf-8").decode(bytes);
  }
}

function parseSse(text: string): unknown[] {
  const values: unknown[] = [];
  const normalized = text.replace(/^\uFEFF/, "").replace(/\r\n?/g, "\n");

  for (const event of normalized.split(/\n\n+/)) {
    const data = event
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).replace(/^ /, ""))
      .join("\n")
      .trim();
    if (!data || data === "[DONE]") continue;
    try {
      values.push(JSON.parse(data));
    } catch (error) {
      throw new Error(`invalid SSE JSON payload: ${errorMessage(error)}`);
    }
  }

  if (values.length === 0) throw new Error("SSE response contained no data events");
  return values;
}

function parseJsonOrSse(text: string, contentType: string): unknown {
  const trimmed = text.replace(/^\uFEFF/, "").trim();
  if (!trimmed) throw new Error("provider returned an empty response");

  if (/text\/event-stream/i.test(contentType) || /^(?:event:|data:)/m.test(trimmed)) {
    const events = parseSse(trimmed);
    return events.findLast((event) => {
      const value = event as JsonRpcEnvelope;
      return value && typeof value === "object" && ("result" in value || "error" in value);
    }) ?? events.at(-1);
  }

  try {
    return JSON.parse(trimmed);
  } catch (error) {
    throw new Error(`provider returned invalid JSON: ${errorMessage(error)}`);
  }
}

function rpcResultText(payload: unknown): string {
  const envelope = payload as JsonRpcEnvelope;
  if (!envelope || typeof envelope !== "object") throw new Error("provider returned an invalid JSON-RPC response");
  if (envelope.error) {
    const code = envelope.error.code === undefined ? "" : ` (${String(envelope.error.code)})`;
    const message = typeof envelope.error.message === "string" ? envelope.error.message : "unknown JSON-RPC error";
    throw new Error(`Exa JSON-RPC error${code}: ${message}`);
  }
  if (!("result" in envelope)) throw new Error("Exa JSON-RPC response did not contain a result");

  const result = envelope.result as { content?: unknown; isError?: unknown } | undefined;
  if (result?.isError === true) {
    const summary = Array.isArray(result.content)
      ? result.content
          .flatMap((item) => item && typeof item === "object" && typeof (item as { text?: unknown }).text === "string" ? [(item as { text: string }).text] : [])
          .join("\n")
      : "";
    throw new Error(`Exa tool error${summary ? `: ${summary}` : ""}`);
  }
  if (result && Array.isArray(result.content)) {
    const parts = result.content.flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const value = item as { type?: unknown; text?: unknown; resource?: { text?: unknown } };
      if (typeof value.text === "string") return [value.text];
      if (typeof value.resource?.text === "string") return [value.resource.text];
      return [];
    });
    if (parts.length > 0) return parts.join("\n\n");
  }
  return typeof envelope.result === "string" ? envelope.result : (JSON.stringify(envelope.result, null, 2) ?? "null");
}

async function providerRequest(
  url: string,
  init: RequestInit,
  signal: AbortSignal | undefined,
  timeoutMs: number,
  label: string,
): Promise<{ payload: unknown; response: Response }> {
  const request = createRequestSignal(signal, timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: request.signal, redirect: "follow" });
    const bytes = await readResponseBytes(response, FETCH_MAX_BYTES);
    const text = decodeBytes(bytes, response.headers.get("content-type") ?? "");
    if (!response.ok) {
      const summary = text.trim().replace(/\s+/g, " ").slice(0, 500);
      throw new Error(`${label} returned HTTP ${response.status} ${response.statusText}${summary ? `: ${summary}` : ""}`);
    }
    return { payload: parseJsonOrSse(text, response.headers.get("content-type") ?? ""), response };
  } catch (error) {
    if (request.timedOut()) throw new Error(`${label} timed out after ${timeoutMs / 1_000}s`);
    if (signal?.aborted) throw new Error(`${label} was cancelled`);
    if (error instanceof Error && error.message.startsWith(label)) throw error;
    throw new Error(`${label} failed: ${errorMessage(error)}`);
  } finally {
    request.cleanup();
  }
}

function isPrivateAddress(address: string): boolean {
  const normalized = address.toLowerCase().replace(/^\[|\]$/g, "");
  if (normalized === "::" || normalized === "::1") return true;
  if (normalized.startsWith("::ffff:")) return true;
  if (normalized.startsWith("fc") || normalized.startsWith("fd") || /^fe[89a-f]/.test(normalized)) return true;
  const mapped = /^::ffff:(\d+\.\d+\.\d+\.\d+)$/.exec(normalized)?.[1];
  const ipv4 = mapped ?? (isIP(normalized) === 4 ? normalized : undefined);
  if (!ipv4) return false;
  const octets = ipv4.split(".").map(Number);
  const [a, b] = octets;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168) ||
    (a === 198 && (b === 18 || b === 19)) ||
    a >= 224
  );
}

interface ResolvedDestination {
  hostname: string;
  address: string;
  family: number;
}

interface PublicResponse {
  status: number;
  statusText: string;
  headers: Record<string, string | string[] | undefined>;
  bytes: Uint8Array;
  finalUrl: URL;
}

async function resolvePublicHttpDestination(url: URL): Promise<ResolvedDestination> {
  if (url.protocol !== "http:" && url.protocol !== "https:") throw new Error(`disallowed protocol ${url.protocol}`);
  if (url.username || url.password) throw new Error("credentials embedded in URLs are not permitted");
  const hostname = url.hostname.replace(/^\[|\]$/g, "");
  if (!hostname || hostname.toLowerCase() === "localhost" || hostname.toLowerCase().endsWith(".localhost")) {
    throw new Error("local destinations are not permitted");
  }
  const literalFamily = isIP(hostname);
  const addresses = literalFamily
    ? [{ address: hostname, family: literalFamily }]
    : await lookup(hostname, { all: true, verbatim: true });
  if (addresses.length === 0) throw new Error(`could not resolve ${hostname}`);
  const blocked = addresses.find(({ address }) => isPrivateAddress(address));
  if (blocked) throw new Error(`destination ${hostname} resolves to a private or non-routable address (${blocked.address})`);
  return { hostname, address: addresses[0]!.address, family: addresses[0]!.family };
}

function headerValue(headers: PublicResponse["headers"], name: string): string | undefined {
  const value = headers[name.toLowerCase()];
  return Array.isArray(value) ? value[0] : value;
}

async function requestPublicUrlOnce(url: URL, signal: AbortSignal | undefined): Promise<PublicResponse> {
  const destination = await resolvePublicHttpDestination(url);
  return new Promise<PublicResponse>((resolve, reject) => {
    const request = url.protocol === "https:" ? httpsRequest : httpRequest;
    const req = request(
      {
        protocol: url.protocol,
        hostname: destination.address,
        family: destination.family,
        port: url.port || undefined,
        path: `${url.pathname}${url.search}`,
        method: "GET",
        servername: url.protocol === "https:" ? destination.hostname : undefined,
        headers: {
          accept: "text/html, text/plain, application/json, application/xml, image/*;q=0.9, */*;q=0.1",
          host: url.host,
          "user-agent": USER_AGENT,
        },
      },
      (response) => {
        const chunks: Buffer[] = [];
        let size = 0;
        response.on("data", (chunk: Buffer) => {
          size += chunk.byteLength;
          if (size > FETCH_MAX_BYTES) {
            response.destroy(new Error(`response exceeded the ${formatSize(FETCH_MAX_BYTES)} maximum`));
            return;
          }
          chunks.push(chunk);
        });
        response.on("end", () => {
          cleanup();
          resolve({
            status: response.statusCode ?? 0,
            statusText: response.statusMessage ?? "",
            headers: response.headers,
            bytes: Buffer.concat(chunks),
            finalUrl: url,
          });
        });
        response.on("error", (error) => {
          cleanup();
          reject(error);
        });
      },
    );
    const onAbort = () => req.destroy(signal?.reason instanceof Error ? signal.reason : new Error("Cancelled"));
    const cleanup = () => signal?.removeEventListener("abort", onAbort);
    req.on("error", (error) => {
      cleanup();
      reject(error);
    });
    if (signal?.aborted) onAbort();
    else signal?.addEventListener("abort", onAbort, { once: true });
    req.end();
  });
}

async function fetchPublicUrl(url: URL, signal: AbortSignal | undefined): Promise<PublicResponse> {
  let current = url;
  for (let redirects = 0; redirects <= FETCH_MAX_REDIRECTS; redirects += 1) {
    const response = await requestPublicUrlOnce(current, signal);
    if (![301, 302, 303, 307, 308].includes(response.status)) return response;
    const location = headerValue(response.headers, "location");
    if (!location) throw new Error(`redirect from ${current.toString()} did not include a Location header`);
    if (redirects === FETCH_MAX_REDIRECTS) throw new Error(`too many redirects (maximum ${FETCH_MAX_REDIRECTS})`);
    current = new URL(location, current);
  }
  throw new Error("redirect handling failed");
}

function selectedSearchProvider(): SearchProvider {
  const configured = (process.env.PI_WEB_SEARCH_PROVIDER ?? "exa").trim().toLowerCase();
  if (configured !== "exa" && configured !== "parallel") {
    throw new Error(`PI_WEB_SEARCH_PROVIDER must be "exa" or "parallel" (received ${JSON.stringify(configured)})`);
  }
  return configured;
}

interface SearchOptions {
  query: string;
  numResults?: number;
  livecrawl?: "fallback" | "preferred";
  type?: "auto" | "fast" | "deep";
  contextMaxCharacters?: number;
}

async function searchWeb(options: SearchOptions, signal: AbortSignal | undefined): Promise<{ provider: SearchProvider; text: string }> {
  const provider = selectedSearchProvider();
  const query = options.query;

  if (provider === "exa") {
    const apiKey = process.env.EXA_API_KEY?.trim();
    const endpoint = new URL(EXA_MCP_URL);
    if (apiKey) endpoint.searchParams.set("exaApiKey", apiKey);
    const { payload } = await providerRequest(
      endpoint.toString(),
      {
        method: "POST",
        headers: {
          accept: "application/json, text/event-stream",
          "content-type": "application/json",
          "user-agent": USER_AGENT,
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: `pi-${Date.now()}`,
          method: "tools/call",
          params: {
            name: "web_search_exa",
            arguments: {
              query,
              type: options.type ?? "auto",
              numResults: options.numResults ?? 8,
              livecrawl: options.livecrawl ?? "fallback",
              contextMaxCharacters: options.contextMaxCharacters ?? 10_000,
            },
          },
        }),
      },
      signal,
      SEARCH_TIMEOUT_MS,
      "Exa search",
    );
    return { provider, text: rpcResultText(payload) };
  }

  const apiKey = process.env.PARALLEL_API_KEY?.trim();
  const { payload } = await providerRequest(
    PARALLEL_SEARCH_URL,
    {
      method: "POST",
      headers: {
        accept: "application/json, text/event-stream",
        "content-type": "application/json",
        "user-agent": USER_AGENT,
        ...(apiKey ? { authorization: `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: `pi-${Date.now()}`,
        method: "tools/call",
        params: {
          name: "web_search",
          arguments: {
            objective: query,
            search_queries: [query],
            max_results: options.numResults ?? 8,
          },
        },
      }),
    },
    signal,
    SEARCH_TIMEOUT_MS,
    "Parallel search",
  );
  return { provider, text: rpcResultText(payload) };
}

const NAMED_ENTITIES: Record<string, string> = {
  amp: "&",
  apos: "'",
  gt: ">",
  hellip: "…",
  laquo: "«",
  ldquo: "“",
  lsquo: "‘",
  lt: "<",
  mdash: "—",
  nbsp: " ",
  ndash: "–",
  quot: '"',
  raquo: "»",
  rdquo: "”",
  rsquo: "’",
};

function decodeHtmlEntities(value: string): string {
  return value.replace(/&(#(?:x[0-9a-f]+|\d+)|[a-z][a-z0-9]+);/gi, (match, entity: string) => {
    if (entity[0] === "#") {
      const hexadecimal = entity[1]?.toLowerCase() === "x";
      const codePoint = Number.parseInt(entity.slice(hexadecimal ? 2 : 1), hexadecimal ? 16 : 10);
      if (Number.isFinite(codePoint) && codePoint >= 0 && codePoint <= 0x10ffff) {
        try {
          return String.fromCodePoint(codePoint);
        } catch {
          return "�";
        }
      }
      return "�";
    }
    return NAMED_ENTITIES[entity.toLowerCase()] ?? match;
  });
}

function stripTags(value: string): string {
  return decodeHtmlEntities(value.replace(/<[^>]*>/g, " ")).replace(/[\t ]+/g, " ").trim();
}

function resolveLink(href: string, baseUrl: string): string {
  const decoded = decodeHtmlEntities(href).trim();
  if (!decoded || /^(?:javascript|data|vbscript):/i.test(decoded)) return "";
  try {
    const resolved = new URL(decoded, baseUrl);
    return ["http:", "https:", "mailto:"].includes(resolved.protocol) ? resolved.toString() : "";
  } catch {
    return "";
  }
}

function htmlToMarkdown(html: string, baseUrl: string): { title?: string; markdown: string } {
  const title = stripTags(/<title\b[^>]*>([\s\S]*?)<\/title>/i.exec(html)?.[1] ?? "") || undefined;
  let output = html
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<(script|style|template|noscript|svg)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "")
    .replace(/<pre\b[^>]*>([\s\S]*?)<\/pre\s*>/gi, (_match, body: string) => `\n\n\`\`\`\n${stripTags(body)}\n\`\`\`\n\n`)
    .replace(/<code\b[^>]*>([\s\S]*?)<\/code\s*>/gi, (_match, body: string) => `\`${stripTags(body).replace(/`/g, "\\`")}\``)
    .replace(/<a\b[^>]*href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>([\s\S]*?)<\/a\s*>/gi,
      (_match, double: string, single: string, bare: string, body: string) => {
        const label = stripTags(body);
        const href = resolveLink(double ?? single ?? bare ?? "", baseUrl);
        return href ? `[${label || href}](${href})` : label;
      })
    .replace(/<img\b[^>]*alt\s*=\s*(?:"([^"]*)"|'([^']*)')[^>]*>/gi, (_match, double: string, single: string) =>
      double || single ? ` ${decodeHtmlEntities(double ?? single)} ` : " ")
    .replace(/<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1\s*>/gi,
      (_match, level: string, body: string) => `\n\n${"#".repeat(Number(level))} ${stripTags(body)}\n\n`)
    .replace(/<li\b[^>]*>([\s\S]*?)<\/li\s*>/gi, (_match, body: string) => `\n- ${stripTags(body)}`)
    .replace(/<blockquote\b[^>]*>([\s\S]*?)<\/blockquote\s*>/gi,
      (_match, body: string) => `\n\n> ${stripTags(body)}\n\n`)
    .replace(/<br\s*\/?\s*>/gi, "\n")
    .replace(/<\/(?:p|div|section|article|main|header|footer|aside|nav|ul|ol|table|tr|figure|figcaption)\s*>/gi, "\n\n")
    .replace(/<(?:p|div|section|article|main|header|footer|aside|nav|ul|ol|table|tr|td|th|figure|figcaption)\b[^>]*>/gi, "\n")
    .replace(/<[^>]*>/g, " ");

  output = decodeHtmlEntities(output)
    .replace(/\u00a0/g, " ")
    .replace(/[\t ]+\n/g, "\n")
    .replace(/\n[\t ]+/g, "\n")
    .replace(/[\t ]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return { title, markdown: output };
}

function markdownToText(markdown: string): string {
  return markdown
    .replace(/\[([^\]]*)\]\(([^)]+)\)/g, "$1 ($2)")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^>\s?/gm, "")
    .replace(/^[-*+]\s+/gm, "• ")
    .replace(/```(?:[^\n]*)\n?/g, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function sniffContentType(bytes: Uint8Array): string {
  if (bytes.length === 0) return "text/plain";
  const sample = bytes.subarray(0, Math.min(bytes.length, 1_024));
  let suspiciousControls = 0;
  for (const byte of sample) {
    if (byte === 0) throw new Error("web_fetch cannot safely decode a response with no Content-Type as text");
    if (byte < 0x09 || (byte > 0x0d && byte < 0x20)) suspiciousControls += 1;
  }
  if (suspiciousControls / sample.length > 0.02) {
    throw new Error("web_fetch cannot safely decode a binary response with no Content-Type");
  }

  const prefix = new TextDecoder("utf-8").decode(sample).trimStart();
  if (/^(?:<!doctype\s+html|<html\b)/i.test(prefix)) return "text/html";
  if (/^[{\[]/.test(prefix)) {
    try {
      JSON.parse(new TextDecoder("utf-8").decode(bytes));
      return "application/json";
    } catch {
      // It remains valid plain text even if it resembles incomplete JSON.
    }
  }
  return "text/plain";
}

function textualBody(raw: string, contentType: string, url: string, format: FetchFormat): { title?: string; body: string } {
  if (/text\/html|application\/xhtml\+xml/i.test(contentType)) {
    if (format === "html") return { body: raw };
    const converted = htmlToMarkdown(raw, url);
    return { title: converted.title, body: format === "text" ? markdownToText(converted.markdown) : converted.markdown };
  }

  if (/application\/(?:[\w.+-]*\+)?json/i.test(contentType)) {
    try {
      return { body: JSON.stringify(JSON.parse(raw), null, 2) };
    } catch {
      return { body: raw };
    }
  }

  if (/^(?:text\/|application\/(?:xml|[\w.+-]*\+xml|javascript|x-javascript))/i.test(contentType) || !contentType) {
    return { body: raw };
  }
  throw new Error(`web_fetch does not support content type ${contentType || "(missing)"}`);
}

function supportedImageType(contentType: string): string | undefined {
  const mime = contentType.split(";", 1)[0]!.trim().toLowerCase();
  return ["image/png", "image/jpeg", "image/gif", "image/webp"].includes(mime) ? mime : undefined;
}

async function truncateOutput(
  output: string,
  details: OutputDetails,
  signal: AbortSignal | undefined,
  operation: "web_search" | "web_fetch",
): Promise<string> {
  if (signal?.aborted) throw new Error(`${operation} was cancelled`);
  const truncation = truncateHead(output, { maxLines: DEFAULT_MAX_LINES, maxBytes: DEFAULT_MAX_BYTES });
  if (!truncation.truncated) return output;

  details.truncated = truncation;
  let storageNotice = " Full output could not be saved.";
  try {
    const directory = await mkdtemp(join(tmpdir(), "pi-web-tools-"));
    const path = join(directory, "output.txt");
    await writeFile(path, output, { encoding: "utf8", mode: 0o600, flag: "wx", signal });
    details.fullOutputPath = path;
    storageNotice = ` Full output saved to: ${path}`;
  } catch {
    if (signal?.aborted) throw new Error(`${operation} was cancelled`);
    // Truncation still protects model context if secure temporary storage is unavailable.
  }

  const prefix = truncation.content ? `${truncation.content}\n\n` : "";
  return `${prefix}[Output truncated: showing ${truncation.outputLines} of ${truncation.totalLines} lines (${formatSize(truncation.outputBytes)} of ${formatSize(truncation.totalBytes)}).${storageNotice}]`;
}

function resultSummary(details: OutputDetails): string {
  if (details.kind === "search") return `${details.provider ?? "web"} search complete${details.truncated ? " (truncated)" : ""}`;
  if (details.image) return `${details.contentType ?? "image"} · ${formatSize(details.bytes ?? 0)}`;
  return `${details.contentType ?? "content"} · ${formatSize(details.bytes ?? 0)}${details.truncated ? " · truncated" : ""}`;
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "web_search",
    label: "Web Search",
    description: `Search the web through Exa by default, or Parallel when PI_WEB_SEARCH_PROVIDER=parallel. EXA_API_KEY and PARALLEL_API_KEY are optional service credentials. Output is truncated to ${DEFAULT_MAX_LINES} lines or ${formatSize(DEFAULT_MAX_BYTES)}.`,
    promptSnippet: "Search the public web with Exa or Parallel",
    parameters: WebSearchParams,
    async execute(_toolCallId, params, signal) {
      const query = params.query.trim();
      if (!query) throw new Error("web_search query must not be blank");
      const search = await searchWeb({ ...params, query }, signal);
      const details: OutputDetails = { kind: "search", provider: search.provider };
      const text = await truncateOutput(search.text, details, signal, "web_search");
      return { content: [{ type: "text", text }], details };
    },
    renderCall(args, theme) {
      const query = args.query.length > 100 ? `${args.query.slice(0, 97)}…` : args.query;
      return new Text(`${theme.fg("toolTitle", theme.bold("web_search "))}${theme.fg("muted", query)}`, 0, 0);
    },
    renderResult(result, { isPartial }, theme) {
      if (isPartial) return new Text(theme.fg("warning", "Searching…"), 0, 0);
      const details = result.details as OutputDetails | undefined;
      return new Text(theme.fg(details?.truncated ? "warning" : "success", details ? resultSummary(details) : "Search complete"), 0, 0);
    },
  });

  pi.registerTool({
    name: "web_fetch",
    label: "Web Fetch",
    description: `Fetch a public http/https URL with validated redirects and convert HTML to dependency-free readable markdown or text. Private/local destinations are blocked. Responses are limited to ${formatSize(FETCH_MAX_BYTES)}, images to ${formatSize(FETCH_MAX_IMAGE_BYTES)}, and model text to ${DEFAULT_MAX_LINES} lines or ${formatSize(DEFAULT_MAX_BYTES)}.`,
    promptSnippet: "Fetch an http/https page as readable markdown, text, HTML, JSON, or an image",
    parameters: WebFetchParams,
    async execute(_toolCallId, params, signal) {
      let requestedUrl: URL;
      try {
        requestedUrl = new URL(params.url);
      } catch {
        throw new Error(`web_fetch requires a valid absolute URL (received ${JSON.stringify(params.url)})`);
      }
      if (requestedUrl.protocol !== "http:" && requestedUrl.protocol !== "https:") {
        throw new Error(`web_fetch only permits http and https URLs (received ${requestedUrl.protocol})`);
      }
      if (requestedUrl.username || requestedUrl.password) {
        throw new Error("web_fetch does not permit credentials embedded in URLs");
      }

      const timeoutSeconds = params.timeout ?? FETCH_DEFAULT_TIMEOUT_SECONDS;
      const request = createRequestSignal(signal, timeoutSeconds * 1_000);
      try {
        const response = await fetchPublicUrl(requestedUrl, request.signal);
        const finalUrl = response.finalUrl.toString();
        const bytes = response.bytes;
        const contentType = headerValue(response.headers, "content-type") ?? "";
        if (response.status < 200 || response.status >= 300) {
          const summary = decodeBytes(bytes, contentType).trim().replace(/\s+/g, " ").slice(0, 500);
          throw new Error(`HTTP ${response.status} ${response.statusText}${summary ? `: ${summary}` : ""}`);
        }

        const imageType = supportedImageType(contentType);
        if (imageType) {
          if (bytes.byteLength > FETCH_MAX_IMAGE_BYTES) {
            throw new Error(`image is too large for model context (${formatSize(bytes.byteLength)}; maximum ${formatSize(FETCH_MAX_IMAGE_BYTES)})`);
          }
          const details: OutputDetails = { kind: "fetch", url: finalUrl, contentType: imageType, bytes: bytes.byteLength, image: true };
          return {
            content: [
              { type: "text", text: `Fetched image from ${finalUrl} (${imageType}, ${formatSize(bytes.byteLength)}).` },
              { type: "image", data: Buffer.from(bytes).toString("base64"), mimeType: imageType },
            ],
            details,
          };
        }

        if (signal?.aborted) throw new Error("web_fetch was cancelled");
        const declaredType = contentType.split(";", 1)[0]!.trim().toLowerCase();
        const normalizedType = declaredType || sniffContentType(bytes);
        const raw = decodeBytes(bytes, contentType);
        const format = (params.format ?? "markdown") as FetchFormat;
        const converted = textualBody(raw, normalizedType, finalUrl, format);
        const heading = converted.title && format === "markdown" ? `# ${converted.title}\n\n` : converted.title ? `${converted.title}\n\n` : "";
        const output = `${heading}Source: ${finalUrl}\nContent-Type: ${normalizedType || "unknown"}\n\n${converted.body}`;
        const details: OutputDetails = { kind: "fetch", url: finalUrl, contentType: normalizedType || undefined, bytes: bytes.byteLength };
        const text = await truncateOutput(output, details, signal, "web_fetch");
        return { content: [{ type: "text", text }], details };
      } catch (error) {
        if (request.timedOut()) throw new Error(`web_fetch timed out after ${timeoutSeconds}s`);
        if (signal?.aborted) throw new Error("web_fetch was cancelled");
        if (error instanceof Error && error.message.startsWith("web_fetch")) throw error;
        throw new Error(`web_fetch failed for ${requestedUrl.toString()}: ${errorMessage(error)}`);
      } finally {
        request.cleanup();
      }
    },
    renderCall(args, theme) {
      const url = args.url.length > 100 ? `${args.url.slice(0, 97)}…` : args.url;
      return new Text(`${theme.fg("toolTitle", theme.bold("web_fetch "))}${theme.fg("muted", url)}`, 0, 0);
    },
    renderResult(result, { isPartial }, theme) {
      if (isPartial) return new Text(theme.fg("warning", "Fetching…"), 0, 0);
      const details = result.details as OutputDetails | undefined;
      return new Text(theme.fg(details?.truncated ? "warning" : "success", details ? resultSummary(details) : "Fetch complete"), 0, 0);
    },
  });
}
