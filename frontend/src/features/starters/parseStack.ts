import { MODULES, STACK_FIELDS, type StackChoiceInput } from "./types";

const NAME = /^[\w .#+-]{1,40}$/;

/** Reads the stack fields of a form (StackFields). Empty fields are the team's to decide. */
export function parseStack(form: FormData): StackChoiceInput | { error: string } {
  const stack: StackChoiceInput = {};
  for (const field of STACK_FIELDS) {
    const value = String(form.get(`stack_${field}`) ?? "").trim();
    if (!value) continue;
    if (!NAME.test(value)) return { error: `Keep the ${field} choice to a short name.` };
    stack[field] = value;
  }
  const modules = MODULES.map((m) => m.name).filter((name) => form.get(`module_${name}`) === "on");
  if (modules.length) stack.modules = modules;
  const starter = String(form.get("stack_starter") ?? "auto");
  if (starter === "yes" || starter === "no") stack.starter = starter === "yes";
  const notes = String(form.get("stack_notes") ?? "").trim();
  if (notes.length > 3000) return { error: "Keep the stack notes under 3,000 characters." };
  if (notes) stack.notes = notes;
  return stack;
}
