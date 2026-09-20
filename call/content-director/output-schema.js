import { visualSchema } from "./visual-prompts.js";
// Provider-side structure prevents unescaped Arabic prose from breaking JSON.
// Semantic validation (timing, readability, quality) still runs after generation.
const string = { type: "string" };
const number = { type: "number" };
const object = (properties) => ({
  type: "object",
  properties,
  required: Object.keys(properties),
  additionalProperties: false,
});
const strings = (keys) =>
  Object.fromEntries(keys.split(" ").map((k) => [k, string]));
const array = (items) => ({ type: "array", items });

export function outputSchema(stage, context) {
  const visual = visualSchema(stage);
  if (visual) return visual;
  if (stage !== "storyboard") return undefined;
  const duration = context?.proposal?.duration_seconds;
  return object({
    duration_seconds: {
      type: "integer",
      ...(Number.isInteger(duration) ? { enum: [duration] } : {}),
    },
    scenes: {
      ...array(
        object({
          id: string,
          start: number,
          end: number,
          ...strings(
            "visual framing focal_point camera action performance lighting sound transition transition_reason emotion purpose production_note",
          ),
        }),
      ),
      minItems: 3,
    },
    beats: {
      ...array(
        object({
          start: number,
          end: number,
          ...strings("shot_id visual_change sound_change emotion purpose"),
        }),
      ),
      // Do not unroll a large fixed-length tuple in the provider grammar.
      // Exact per-second coverage is enforced by validateStoryboard locally.
    },
    voiceover: array(
      object({ start: number, end: number, text: string, delivery: string }),
    ),
    screen_text: array(object({ start: number, end: number, text: string })),
  });
}
