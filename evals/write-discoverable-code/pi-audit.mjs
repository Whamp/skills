/** Record the effective benchmark profile without loading ambient extensions. */
export default function registerDiscoveryAudit(pi) {
  const profile = (ctx) => ({
    type: "eval_profile",
    systemPrompt: ctx.getSystemPrompt(),
    tools: pi.getActiveTools(),
    provider: ctx.model?.provider,
    model: ctx.model?.id,
    thinking: pi.getThinkingLevel(),
  });

  pi.registerCommand("eval-profile", {
    description: "Inspect the benchmark profile without calling a model",
    handler: async (_args, ctx) => {
      console.log(
        JSON.stringify({
          ...profile(ctx),
          options: ctx.getSystemPromptOptions(),
          messageCount: ctx.sessionManager.getBranch().filter((entry) => entry.type === "message")
            .length,
        }),
      );
      ctx.shutdown();
    },
  });

  pi.on("before_agent_start", (_event, ctx) => {
    console.log(JSON.stringify(profile(ctx)));
  });

  let calls = 0;
  pi.on("tool_call", () => {
    calls += 1;
    if (calls > Number(process.env.DISCOVERY_MAX_CALLS)) {
      return { block: true, reason: "The benchmark tool-call budget is exhausted." };
    }
  });
}
