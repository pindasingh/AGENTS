import type { Model, Provider } from "@earendil-works/pi-ai";
import { opencodeGoProvider } from "@earendil-works/pi-ai/providers/opencode-go";
import { opencodeProvider } from "@earendil-works/pi-ai/providers/opencode";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * Presents OpenCode Zen and OpenCode Go as one provider.
 *
 * Both products use the same OpenCode credential. Go models override Zen models
 * with the same id; models available only in Zen remain available alongside them.
 */
export default function (pi: ExtensionAPI) {
	const zen = opencodeProvider();
	const go = opencodeGoProvider();
	const models = new Map<string, Model>();
	const goModelIds = new Set(go.getModels().map((model) => model.id));

	for (const model of [...zen.getModels(), ...go.getModels()]) {
		models.set(model.id, { ...model, provider: "opencode" });
	}

	const provider: Provider = {
		id: "opencode",
		name: "opencode",
		auth: zen.auth,
		getModels: () => [...models.values()],
		stream: (model, context, options) =>
			goModelIds.has(model.id) ? go.stream(model, context, options) : zen.stream(model, context, options),
		streamSimple: (model, context, options) =>
			goModelIds.has(model.id)
				? go.streamSimple(model, context, options)
				: zen.streamSimple(model, context, options),
	};

	pi.registerProvider(provider);

	// Built-ins are installed after extension factories in some Pi versions.
	// Remove the split provider from the live runtime, not merely its extension
	// override (which would reveal the built-in provider again).
	pi.on("session_start", (_event, ctx) => {
		const runtime = (
			ctx.modelRegistry as unknown as {
				runtime: {
					builtins: Map<string, Provider>;
					defaultBuiltins: Map<string, Provider>;
					nativeExtensionProviders: Map<string, Provider>;
					rebuildProviders(): void;
				};
			}
		).runtime;

		runtime.builtins.delete("opencode-go");
		runtime.defaultBuiltins.delete("opencode-go");
		runtime.nativeExtensionProviders.delete("opencode-go");
		runtime.rebuildProviders();
		ctx.modelRegistry.registerProvider(provider);
	});
}
