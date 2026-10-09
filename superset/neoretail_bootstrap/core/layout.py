"""Shared layout helpers extracted without changing defaults."""
from __future__ import annotations


class Layout:
    def __init__(self):
        self.nodes = {
            "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
            "GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []},
        }
        self.counter = 0

    def _id(self, prefix):
        self.counter += 1
        return f"{prefix}-{self.counter}"

    def tabs(self, parent, parents, title, entries, height=52):
        tabs_id = self._id("TABS")
        tab_ids = []
        self.nodes[tabs_id] = {"id": tabs_id, "type": "TABS", "parents": parents, "children": tab_ids, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(tabs_id)
        for label, chart_rows in entries:
            tab_id = self._id("TAB")
            tab_ids.append(tab_id)
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": [*parents, tabs_id], "children": [], "meta": {"text": label}}
            for row_charts in chart_rows:
                # A compact, full-width control bar precedes the tall KPI
                # hierarchy charts. All other layouts retain their heights.
                row_height = row_charts.get("height", height) if isinstance(row_charts, dict) else height
                content = row_charts["charts"] if isinstance(row_charts, dict) else row_charts
                self.row(tab_id, [*parents, tabs_id, tab_id], content, row_height)
        return tabs_id

    def period_tabs(self, parent, parents, title, entries, height=52):
        """Render business views with an inner Mensal/Semanal selector."""
        outer_id = self._id("TABS")
        outer_tabs = []
        self.nodes[outer_id] = {"id": outer_id, "type": "TABS", "parents": parents, "children": outer_tabs, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(outer_id)
        for label, periods in entries:
            tab_id = self._id("TAB")
            outer_tabs.append(tab_id)
            tab_parents = [*parents, outer_id]
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": tab_parents, "children": [], "meta": {"text": label}}
            self.tabs(tab_id, [*tab_parents, tab_id], f"Período de {label}", [
                (period.title(), [[*chart] if isinstance(chart, (list, tuple)) else [chart]])
                for period, chart in periods
            ], height)
        return outer_id

    def row(self, parent, parents, charts, height):
        row_id = self._id("ROW")
        children = []
        self.nodes[row_id] = {"id": row_id, "type": "ROW", "parents": parents, "children": children, "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        self.nodes[parent]["children"].append(row_id)
        widths = [3, 9] if len(charts) == 2 and "Resumo" in charts[0].slice_name else [max(1, 12 // len(charts))] * len(charts)
        for chart, width in zip(charts, widths):
            chart_id = f"CHART-{chart.id}"
            children.append(chart_id)
            self.nodes[chart_id] = {"id": chart_id, "type": "CHART", "parents": [*parents, row_id], "children": [], "meta": {"chartId": chart.id, "height": height, "width": width, "sliceName": chart.slice_name, "uuid": str(chart.uuid)}}
