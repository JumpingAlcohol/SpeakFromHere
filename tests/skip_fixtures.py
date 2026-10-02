"""Synthetic structures; never copy chat text or file paths into fixtures."""
from probe_fixtures import node


def activity(key="activity"):
    return node(key, css="outline-none", children=(
        node(key+"-inner", css="min-w-0 text-size-chat relative overflow-visible py-0", children=(
            node(key+"-header", css="group/activity-header relative inline-flex", children=(
                node(key+"-label", "description", name="已优化对话"),)),)),))


def edited_files(key="files"):
    header = node(key, css="group/turn-diff-header relative", children=(
        node(key+"-open", "button", css="absolute inset-0 cursor-interaction"),
        node(key+"-icon", "img"),
        node(key+"-count", "description", name="已编辑 2 个文件"),
        node(key+"-subtitle", css="turn-diff-default-subtitle inline-flex", children=(
            node(key+"-added", "description", name="+2"), node(key+"-removed", "description", name="-1"))),
        node(key+"-undo", "button", css="button-toolbar", children=(
            node(key+"-undo-text", "description", name="Synthetic undo"), node(key+"-undo-icon", "img"))),
        node(key+"-review", "button", css="button-toolbar"),))
    rows = tuple(node(key+f"-row-{i}", "button",
        css="flex h-9 w-full text-size-chat py-[var(--turn-diff-row-padding-y)] group-last/turn-diff-file-row:rounded-b-lg",
        children=(node(key+f"-name-{i}", "description", name=f"synthetic-{i}.py"),
                  node(key+f"-plus-{i}", "description", name="+1"),
                  node(key+f"-minus-{i}", "description", name="-0"))) for i in range(2))
    more = node(key+"-more", "button", css="flex w-full text-size-chat py-[var(--turn-diff-row-padding-y)] rounded-b-lg",
                children=(node(key+"-more-text", "description", name="Synthetic view files"),
                          node(key+"-more-icon", "img", css="icon-2xs")))
    return (header, *rows, more)


def table_widget(key="table-widget", style="fixture"):
    """Inspected widget topology, with invented cell text and varying CSS hashes."""
    rows = []
    for row_index in range(2):
        cells = []
        for column in range(2):
            cell_id = f"{key}-{row_index}-{column}"
            cell = node(cell_id, "columnheader" if row_index == 0 else "gridcell",
                        css=f"_TableCell_{style}_2", bounds=(10 + column * 50, 70 + row_index * 10, 50, 10),
                        children=(node(cell_id+"-text", "description", name="Synthetic omitted cell"),))
            cell["control_type"] = 50029
            cells.append(cell)
        row = node(f"{key}-row-{row_index}", "row", css=f"_TableRow_{style}_2", children=cells)
        row["control_type"] = 50029
        rows.append(row)
    grid = node(key+"-grid", "grid", css=f"_Table_{style}_2", bounds=(10, 70, 100, 20), children=rows)
    grid["control_type"] = 50036
    tools = node(key+"-tools", css="absolute group-hover/app-widget:pointer-events-auto group-hover/app-widget:opacity-100",
                 children=tuple(node(key+f"-tool-{index}", css="contents", children=(
                     node(key+f"-action-{index}", "button", css="no-drag cursor-interaction", name="Synthetic table action"),))
                     for index in range(2)))
    return node(key, css=f"group/app-widget _TableContainer_{style}_2", bounds=(10, 70, 100, 20),
                children=(grid, tools))


def standalone_reply_controls(language="zh"):
    retry, more = ("重新生成回复", "更多操作") if language == "zh" else ("Regenerate response", "More actions")
    return (node("retry-leaf", "button", name=retry,
                 css="no-drag cursor-interaction electron:rounded-md electron:p-1 text-tertiary outline-hidden"),
            node("more-leaf", "button", name=more, css="_Button_fixture_2 outline-hidden cursor-interaction"))
