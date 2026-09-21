// Registry: table `source` hint name -> lazily-imported import-source module (MIDAS.md §5).
// The table widget (table-input.js / table-input-events.js) only ever calls `sourceFor(name)`;
// it holds no per-source code, so adding a new import source never touches the generic editor.
//
// Each entry is `{ buttonLabel, load() -> Promise<{ openImport(context) }> }`. `load` is called
// (and its module evaluated) only when the user actually clicks the button, not on page load.
//
// `context` passed to `openImport`: `{ field, columns, table, currentRows, setRows, message,
// trigger }` -- `currentRows`/`setRows` are the same row-state hooks table-input.js already
// threads through its own toolbar; `message` posts into the field's own message area (the
// conduit already used for paste/CSV feedback); `trigger` is the button, so the module can
// return focus to it when it is done (MIDAS.md §5, dialog focus contract).

const SOURCES = {
  "midas-reactions": {
    buttonLabel: "Importa da MIDAS",
    load: () => import("./midas-dialog.js"),
  },
};

export function sourceFor(name) {
  return name ? SOURCES[name] || null : null;
}
