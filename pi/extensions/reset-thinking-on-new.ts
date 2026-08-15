import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("session_start", (event) => {
    if (event.reason === "new") {
      pi.setThinkingLevel("low");
    }
  });
}
