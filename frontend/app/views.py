import datetime
import json
import zoneinfo
from datetime import datetime
from typing import Any, Callable, Optional, Tuple
from urllib.parse import quote

import flet as ft
import humanize
from flet.core.control_event import ControlEvent
from flet.core.types import MainAxisAlignment

from .components.base import (
    Badge,
    Form,
    DateTimeField,
    ConfirmationDialog,
)
from .components.base.external_links_bar import ExternalLinksBar
from .components.base.link import Link
from .components.tests import (
    FileUploadManager,
    FileTile,
    LogbookEntryTile,
    TestStatusBadge,
    TestsFilter,
    TestsTable,
)
from .components.tests.datacard import DataCard
from .components.tests.linklist import LinkList
from .models import LogbookEntry, Test, TestStatus
from .utils.routing import Router, Request
from .store import STORE
from .utils.date import format_date
from .utils.exceptions import ValidationError
from .theme import theme_manager
from .env import SDK_TOKEN, TESTMANAGER_TIMEZONE, get_lake_query_ui_url

# TODO: Add links

PLACEHOLDER = ft.Text("—", color="#999999")

router = Router()

def get_external_links(test_id: str, campaign_id: str, environment_id: str) -> list[Tuple[str, str]]:
    
    lake_querystring = f"&key={test_id}" if test_id else ""
    
    sql = quote(f"SELECT * FROM config-enriched-data\nWHERE campaign_id = '{campaign_id}'\nAND environment_id = '{environment_id}'\nAND test_id = '{test_id}'\nLIMIT 100")
    lake_sql_editor_querystring = f"?token={SDK_TOKEN}&sql={sql}&autorun=true" if test_id else f"?token={SDK_TOKEN}"

    stream_id = f"&stream_id={test_id}" if test_id else ""
    marimo_querystring = f"?token={SDK_TOKEN}&campaign_id={campaign_id}&environment_id={environment_id}&test_id={test_id}" if test_id else f"?token={SDK_TOKEN}"

    return [
        (f"https://portal.cloud.quix.io/pipeline/deployments/65946fb1-70bf-4768-b043-7c9e0f6d710e/embedded?workspace=quixers-testmanagerdemo-dev{stream_id}", "Configuration Manager"),
        (f"https://portal.cloud.quix.io/data?workspace=quixers-aerospacedemoingestionpipeline-prod{lake_querystring}", "Data Lake"),
        (f"{get_lake_query_ui_url()}{lake_sql_editor_querystring}", "Data Query"),
        (f"https://marimo-analysis-quixers-advanceanalyticsdemo-main.az-france-0.app.quix.io/{marimo_querystring}", "Notebook"),
    ]

def _filter_tests(tests: list[Test], filters: dict[str, Any]) -> list[Test]:
    print(f"Filtering with: {filters}")
    filtered = []
    for test in tests:
        match = True
        for field, value in filters.items():
            test_value = getattr(test, field)
            if test_value != value:
                match = False
                break
        if match:
            filtered.append(test)
    return filtered


@router.register("/tests")
def tests_list_view(req: Request) -> ft.Control:
    """
    A view with a list of all tests.
    """

    all_tests = STORE.get_tests()

    filter_fields = {
        "environment_id": "Environment ID",
        "campaign_id": "Campaign ID",
        "sample_id": "Sample ID",
        "operator": "Operator",
    }

    # Store current filter state
    current_filters = {}
    
    # Create containers that we can update
    table_container = ft.Container()
    filters_container = ft.Container()
    
    def update_table(filters: dict[str, str]):
        """Update the table with new filtered data"""
        filtered_tests = _filter_tests(tests=all_tests, filters=filters)
        print(f"Updating table - Total tests: {len(all_tests)}, Filtered tests: {len(filtered_tests)}")
        table_container.content = TestsTable(tests=filtered_tests, router=router).render()
        table_container.update()

    def refresh_data(e: ft.ControlEvent):
        """Refresh the test data from the API"""
        try:
            nonlocal all_tests
            all_tests = STORE.get_tests()
            update_table(current_filters)
            
            # Re-render filters with new data
            filters_container.content = TestsFilter(
                fields=filter_fields,
                values=current_filters,
                tests=all_tests,
                on_filter_change=on_filter_change,
            ).render()
            filters_container.update()
            
            e.page.snack_bar = ft.SnackBar(
                content=ft.Text("Data refreshed successfully"),
                action="OK",
            )
            e.page.snack_bar.open = True
            e.page.update()
        except Exception as ex:
            e.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"),
                action="OK",
                bgcolor=ft.Colors.ERROR,
            )
            e.page.snack_bar.open = True
            e.page.update()

    def on_filter_change(e: ft.ControlEvent, values: dict[str, str]):
        # Only include non-empty values in the query
        nonlocal current_filters
        current_filters = {k: v for k, v in values.items() if v}
        print(f"Filter changed to: {current_filters}")
        
        # Update the table
        update_table(current_filters)
        
        # Re-render the filters to ensure UI is in sync
        filters_container.content = TestsFilter(
            fields=filter_fields,
            values=current_filters,
            tests=all_tests,
            on_filter_change=on_filter_change,
        ).render()
        filters_container.update()

    print(f"Raw query items: {req.query.items()}")
    filter_values = {k: v[0] if isinstance(v, list) else v for k, v in req.query.items() if v}
    print(f"Current filter values from URL: {filter_values}")
    current_filters = filter_values
    
    # Initial filter render
    filters_container.content = TestsFilter(
        fields=filter_fields,
        values=filter_values,
        tests=all_tests,
        on_filter_change=on_filter_change,
    ).render()
    filters_container.padding = ft.padding.symmetric(vertical=10)

    header = ft.Row(
        [
            ft.Row([
                ft.Text("Tests", theme_style=ft.TextThemeStyle.TITLE_LARGE),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh data",
                    on_click=refresh_data,
                    icon_color=theme_manager.colors.active_icon,
                ),
            ]),
            ft.FilledButton(
                text="New test ",
                icon=ft.Icons.ADD,
                on_click=lambda e: e.page.go("/tests/add"),
                bgcolor=theme_manager.colors.button_primary_bg,
                color=theme_manager.colors.button_primary_text
            ),
        ],
        expand=True,
        alignment=MainAxisAlignment.SPACE_BETWEEN,
    )

    # Initial table render
    filtered_tests = _filter_tests(tests=all_tests, filters=filter_values)
    print(f"Total tests: {len(all_tests)}, Filtered tests: {len(filtered_tests)}")
    table_container.content = TestsTable(tests=filtered_tests, router=router).render()

    # External links configuration
    external_links = get_external_links(test_id="", campaign_id="", environment_id="")
    links_bar = ExternalLinksBar(links=external_links).render()
    
    # Schedule auto-refresh after page load
    if hasattr(req, 'page') and req.page:
        import threading
        def delayed_refresh():
            try:
                class Event:
                    page = req.page
                req.page.run_thread(refresh_data, Event())
            except Exception as e:
                print(f"Auto-refresh error: {e}")
        
        # Trigger refresh after 1000ms delay
        threading.Timer(1, delayed_refresh).start()

    return ft.Column(
        controls=[
            header,
            links_bar,
            filters_container,
            table_container,
        ],
        expand=True,
    )


@router.register("/tests/add")
def test_add_view(_: Request) -> ft.Control:
    fields = {
        "test_id": ft.TextField(label="Test ID *"),
        "sample_id": ft.TextField(label="Sample ID *"),
        "campaign_id": ft.TextField(label="Campaign ID *"),
        "environment_id": ft.TextField(label="Environment ID *"),
        "operator": ft.TextField(label="Operator *"),
        "start": DateTimeField(
            label=f"Start date and time in {TESTMANAGER_TIMEZONE} timezone",
            suffix=ft.Icon(ft.Icons.CALENDAR_MONTH),
            width=600,
        ),
        "end": DateTimeField(
            label=f"End date and time in {TESTMANAGER_TIMEZONE} timezone",
            suffix=ft.Icon(ft.Icons.CALENDAR_MONTH),
            width=600,
        ),
        "grafana_url": ft.TextField(
            label="Grafana Dashboard URL",
            hint_text="http://example.com",
        ),
        "sensors": ft.TextField(
            label="Parameters", multiline=True, min_lines=10, align_label_with_hint=True
        ),
    }

    def _on_submit(data: dict[str, Optional[str]]):
        sensors = data.get("sensors")
        if sensors:
            try:
                sensors_json = json.loads(sensors)
            except Exception:
                raise ValidationError(field="sensors", message="Invalid JSON")
            data["sensors"] = sensors_json
        data["start"] = DateTimeField.parse(data.get("start"))
        data["end"] = DateTimeField.parse(data.get("end"))
        test = STORE.add_test(**data)
        return f"/tests/{test.test_id}"

    form = Form(fields=fields, on_submit=_on_submit).render()
    title = ft.Text("Add a test", theme_style=ft.TextThemeStyle.TITLE_LARGE)
    back_button = ft.FilledButton(
        text="Back to Tests",
        icon=ft.Icons.CHEVRON_LEFT,
        bgcolor=theme_manager.colors.button_secondary_bg,
        color=theme_manager.colors.button_secondary_text,
        on_click=lambda e: e.page.go("/tests"),
    )

    # External links configuration
    external_links = get_external_links(test_id="", campaign_id="", environment_id="")
    links_bar = ExternalLinksBar(links=external_links).render()

    return ft.Column(
        [
            # links_bar,
            back_button,
            ft.Card(
                ft.Container(
                    ft.Column(
                        [title, form],
                        spacing=20,
                    ),
                    padding=20,
                ),
                color=theme_manager.colors.card_background,
            ),
        ],
    )


@router.register("/tests/:test_id")
def test_detail_view(req: Request) -> ft.Control:
    test_id = req.params["test_id"]
    test = STORE.get_test(test_id=test_id)

    if test.sensors:
        sensors_text = (
            f"```json\n{json.dumps(test.sensors, indent=2, ensure_ascii=False)}\n```"
        )
        sensors_widget = ft.Column(
            controls=[
                ft.Container(
                    ft.Markdown(
                        sensors_text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK if theme_manager.mode == "dark" else ft.MarkdownCodeTheme.ATOM_ONE_LIGHT,                        expand=True,
                        expand_loose=True,
                    ),
                    expand=True,
                    border_radius=8,
                    bgcolor=theme_manager.colors.card_background,
                )
            ],
            expand=False,
            height=500 if test.sensors else 100,
            scroll=ft.ScrollMode.AUTO,
        )
    else:
        sensors_widget = PLACEHOLDER

    grafana_url_link = (
        Link(url=test.grafana_url).render() if test.grafana_url else PLACEHOLDER
    )
    data = {
        "Test ID": test.test_id,
        "Status": TestStatusBadge(test.status).render(),
        "Campaign ID": test.campaign_id,
        "Environment ID": test.environment_id,
        "Sample ID": test.sample_id,
        "Operator": test.operator,
        "Start date": format_date(test.start) or PLACEHOLDER,
        "End date": format_date(test.end) or PLACEHOLDER,
        "Links": LinkList(links=test.links).render(),
        "Grafana Dashboard URL": grafana_url_link,
        "Created at": format_date(test.created_at),
        "Parameters": sensors_widget,
    }
    back_button = ft.FilledButton(
        text="Back to Tests",
        icon=ft.Icons.CHEVRON_LEFT,
        bgcolor=theme_manager.colors.button_secondary_bg,
        color=theme_manager.colors.button_secondary_text,
        on_click=lambda e: e.page.go("/tests"),
    )
    title = ft.Text(
        f'Test ID "{test.test_id}"',
        theme_style=ft.TextThemeStyle.TITLE_LARGE,
    )
    edit_button = ft.FilledButton(
        "Edit",
        icon=ft.Icons.EDIT,
        bgcolor=theme_manager.colors.button_primary_bg,
        color=theme_manager.colors.button_primary_text,
        on_click=lambda e: e.page.go(
            f"/tests/{test.test_id}/edit",
        ),
    )

    def on_delete(e: ft.ControlEvent):
        def on_submit():
            STORE.delete_test(test_id=test_id)
            e.page.go("/tests")

        dialog = ConfirmationDialog(
            title=ft.Text("Please confirm"),
            content=ft.Text(f'Are you sure you want to delete Test "{test_id}"?'),
            on_confirm=on_submit,
        )
        e.page.open(dialog.render())

    delete_button = ft.OutlinedButton(
        "Delete",
        icon=ft.Icons.DELETE,
        on_click=on_delete,
    )

    test_details = DataCard(data=data, min_leading_width=150, expand=True).render()

    def get_upload_url(filename):
        try:
            return STORE.get_file_upload_url(test_id=test_id, filename=filename)
        except Exception as ex:
            print(f"Error getting upload URL: {ex}")
            raise Exception(f"Failed to get upload URL from server: {str(ex)}")
    
    file_manager = FileUploadManager(
        width=600,
        height=300,
        upload_url_callback=get_upload_url,
        on_success=lambda page: router.refresh(page),
    )
    file_picker = file_manager.render()

    def on_attach_click(e):
        try:
            file_picker.pick_files()
        except Exception as ex:
            print(f"Error opening file picker: {ex}")
            e.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {str(ex)}"))
            e.page.snack_bar.open = True
            e.page.update()
    
    attach_button = ft.FilledButton(
        "Add a file",
        icon=ft.Icons.ATTACH_FILE,
        bgcolor=theme_manager.colors.button_primary_bg,
        color=theme_manager.colors.button_primary_text,
        on_click=on_attach_click,
    )

    test_files = sorted(test.files.values(), key=lambda f: f.uploaded_at, reverse=True)

    files_tiles = [
        FileTile(test_id=test.test_id, router=router, file=f).render()
        for f in test_files
    ] or [
        ft.ListTile(
            expand=True,
            title=ft.Text("No entries"),
            dense=True,
        )
    ]
    files_section = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Files", theme_style=ft.TextThemeStyle.TITLE_LARGE),
                    attach_button,
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            ),
            *files_tiles,
        ],
    )

    logbook_entries = STORE.get_logbook_entries(test_id=test.test_id)

    add_logbook_button = ft.FilledButton(
        "Add an entry",
        icon=ft.Icons.POST_ADD,
        bgcolor=theme_manager.colors.button_primary_bg,
        color=theme_manager.colors.button_primary_text,
        on_click=lambda e: e.page.go(f"/tests/{test.test_id}/logbook/add"),
    )

    logbook_entries_tiles = [
        LogbookEntryTile(entry, router=router).render() for entry in logbook_entries
    ] or [
        ft.ListTile(
            expand=True,
            title=ft.Text("No entries"),
            dense=True,
        )
    ]

    logbook_section = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Testing Log", theme_style=ft.TextThemeStyle.TITLE_LARGE),
                    add_logbook_button,
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            ),
            *logbook_entries_tiles,
        ],
    )

    # External links configuration
    external_links = get_external_links(test_id=test.test_id, campaign_id=test.campaign_id, environment_id=test.environment_id)
    links_bar = ExternalLinksBar(links=external_links).render()
    

    return ft.Container(
        content=ft.Column(
            [
                back_button,
                links_bar,

                ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        title,
                                        ft.Row([edit_button, delete_button]),
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                test_details,
                                files_section,
                                logbook_section,
                                file_picker,
                            ],
                            spacing=20,
                        ),
                        padding=20,
                    ),
                    color=theme_manager.colors.card_background,
                ),
            ],
            spacing=20,
        ),
        bgcolor=theme_manager.colors.background,
        expand=True,
    )


@router.register("/tests/:test_id/edit")
def test_edit_view(req: Request) -> ft.Control:
    test_id = req.params["test_id"]
    test = STORE.get_test(test_id=test_id)

    fields = {
        "campaign_id": ft.TextField(label="Campaign ID *", value=str(test.campaign_id)),
        "environment_id": ft.TextField(
            label="Environment ID *", value=str(test.environment_id)
        ),
        "sample_id": ft.TextField(label="Sample ID *", value=str(test.sample_id)),
        "operator": ft.TextField(label="Operator *", value=str(test.operator)),
        "grafana_url": ft.TextField(
            label="Grafana Dashboard URL",
            value=str(test.grafana_url or ""),
            hint_text="http://example.com",
        ),
        "sensors": ft.TextField(
            label="Parameters",
            multiline=True,
            min_lines=10,
            align_label_with_hint=True,
            value=json.dumps(test.sensors, ensure_ascii=False)
            if test.sensors
            else None,
        ),
    }

    def _on_submit(data: dict[str, str]) -> str:
        sensors = data.get("sensors")
        if sensors:
            try:
                sensors_json = json.loads(sensors)
            except Exception:
                raise ValidationError(field="sensors", message="Invalid JSON")
            data["sensors"] = sensors_json
        STORE.edit_test(test_id=test.test_id, **data)
        return f"/tests/{test.test_id}"

    update_form = Form(fields=fields, on_submit=_on_submit).render()
    back_button = ft.FilledButton(
        text=f"Back to Test {test.test_id}",
        icon=ft.Icons.CHEVRON_LEFT,
        on_click=lambda e: e.page.go(f"/tests/{test.test_id}"),
        bgcolor=theme_manager.colors.button_secondary_bg,
        color=theme_manager.colors.button_secondary_text,
    )
    title = ft.Text(
        f"Edit test {test.test_id}",
        theme_style=ft.TextThemeStyle.TITLE_LARGE,
        selectable=True,
    )
    # External links configuration
    external_links = get_external_links(test_id=test.test_id, campaign_id=test.campaign_id, environment_id=test.environment_id)
    links_bar = ExternalLinksBar(links=external_links).render()
    
    return ft.Container(
        content=ft.Column(
            [
                back_button,
                links_bar,
                ft.Card(
                    ft.Container(
                        ft.Column(
                            [title, update_form],
                            spacing=20,
                        ),
                        padding=20,
                    ),
                    color=theme_manager.colors.card_background,
                ),
            ],
        ),
        bgcolor=theme_manager.colors.background,
        expand=True,
    )


@router.register("/tests/:test_id/logbook/add")
def logbook_add_view(req: Request) -> ft.Control:
    test = STORE.get_test(test_id=req.params["test_id"])
    now = datetime.now(tz=zoneinfo.ZoneInfo(TESTMANAGER_TIMEZONE)).strftime(
        "%d.%m.%Y %H:%M:%S"
    )
    timestamp_field = DateTimeField(
        label=f"Date and time in {TESTMANAGER_TIMEZONE} timezone",
        suffix=ft.Icon(ft.Icons.CALENDAR_MONTH),
        width=600,
        value=now,
    )

    fields = {
        "operator": ft.TextField(label="Operator *", value=test.operator),
        "timestamp": timestamp_field,
        "content": ft.TextField(
            label="Content *",
            multiline=True,
            min_lines=10,
            align_label_with_hint=True,
            hint_text="Post your notes here.",
        ),
        "sensor_ids": ft.TextField(
            label="Parameters",
            hint_text="A comma-separated list of sensor IDs.",
            multiline=True,
            min_lines=2,
            align_label_with_hint=True,
        ),
    }

    def _on_submit(data: dict[str, str]):
        sensor_ids = [
            sensor_id.strip()
            for sensor_id in data.get("sensor_ids", "").split(",")
            if sensor_id.strip()
        ]
        timestamp = timestamp_field.parse(data.get("timestamp"))

        STORE.add_logbook_entry(
            test_id=test.test_id,
            operator=data.get("operator"),
            timestamp=timestamp,
            sensor_ids=sensor_ids,
            content=data.get("content"),
        )
        return f"/tests/{test.test_id}"

    create_form = ft.Column(
        spacing=20,
        controls=[Form(fields=fields, on_submit=_on_submit).render()],
    )
    title = ft.Text("Add a logbook entry", theme_style=ft.TextThemeStyle.TITLE_LARGE)
    back_button = ft.FilledButton(
        text=f"Back to Test {test.test_id}",
        icon=ft.Icons.CHEVRON_LEFT,
        on_click=lambda e: e.page.go(f"/tests/{test.test_id}"),
        bgcolor=theme_manager.colors.button_secondary_bg,
        color=theme_manager.colors.button_secondary_text,
    )
    
    # External links configuration
    external_links = get_external_links(test_id=test.test_id, campaign_id=test.campaign_id, environment_id=test.environment_id)
    links_bar = ExternalLinksBar(links=external_links).render()
    
    return ft.Column(
        [
            links_bar,
            back_button,
            ft.Card(
                ft.Container(
                    ft.Column(
                        [title, create_form],
                        spacing=20,
                    ),
                    padding=20,
                ),
                color=theme_manager.colors.card_background,
            ),
        ],
    )


@router.register("/tests/:test_id/logbook/:entry_id/edit")
def logbook_edit_view(req: Request) -> ft.Control:
    entry = STORE.get_logbook_entry(
        test_id=req.params["test_id"], entry_id=req.params["entry_id"]
    )

    current_timestamp = format_date(entry.timestamp)
    timestamp_field = DateTimeField(
        label=f"Date and time in {TESTMANAGER_TIMEZONE} timezone",
        suffix=ft.Icon(ft.Icons.CALENDAR_MONTH),
        width=600,
        value=current_timestamp,
    )

    fields = {
        "operator": ft.TextField(label="Operator *", value=entry.operator),
        "timestamp": timestamp_field,
        "content": ft.TextField(
            label="Content *",
            multiline=True,
            min_lines=10,
            align_label_with_hint=True,
            hint_text="Post your notes here.",
            value=entry.content,
        ),
        "sensor_ids": ft.TextField(
            label="Parameters",
            hint_text="A comma-separated list of sensor IDs.",
            multiline=True,
            min_lines=2,
            align_label_with_hint=True,
            value=", ".join(entry.sensor_ids),
        ),
    }

    def _on_submit(data: dict[str, str]):
        sensor_ids = [
            sensor_id.strip()
            for sensor_id in data.get("sensor_ids", "").split(",")
            if sensor_id.strip()
        ]
        timestamp = timestamp_field.parse(data.get("timestamp"))

        STORE.update_logbook_entry(
            test_id=entry.test_id,
            entry_id=entry.id,
            operator=data.get("operator"),
            timestamp=timestamp,
            sensor_ids=sensor_ids,
            content=data.get("content"),
        )
        return f"/tests/{entry.test_id}"

    form = Form(fields=fields, on_submit=_on_submit).render()
    title = ft.Text(
        f"Edit a logbook entry at {current_timestamp} for test {entry.test_id}",
        theme_style=ft.TextThemeStyle.TITLE_LARGE,
    )
    back_button = ft.FilledButton(
        text=f"Back to Test {entry.test_id}",
        icon=ft.Icons.CHEVRON_LEFT,
        on_click=lambda e: e.page.go(f"/tests/{entry.test_id}"),
        bgcolor=theme_manager.colors.button_secondary_bg,
        color=theme_manager.colors.button_secondary_text,
    )
    
    # External links configuration
    external_links = get_external_links(test_id=entry.test_id, campaign_id=entry.campaign_id, environment_id=entry.environment_id)
    links_bar = ExternalLinksBar(links=external_links).render()
    
    return ft.Column(
        [
            links_bar,
            back_button,
            ft.Card(
                ft.Container(
                    ft.Column(
                        [title, form],
                        spacing=20,
                    ),
                    padding=20,
                ),
                color=theme_manager.colors.card_background,
            ),
        ],
    )


@router.register("/")
def home_view(_: Request) -> ft.Control:
    intro = ft.Markdown(
        """
# Welcome to Test Manager.

The platform is designed to help engineers efficiently store, access, and analyze test measurements by attaching searchable metadata to every test.
            """,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )

    features = ft.Markdown(
        """
## What you can do with Test Manager:

- **Connect test metadata with results**: Create tests with metadata like environment names, sample IDs, operator names, and link them to the Grafana dasboards with test results.
- **Log test progress**: Keep your test notes in the Testing log for simple analysis.
- **Upload attachments**: Attach relevant files to the tests.
        """,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )

    tests_icon_link = ft.Row(
        [
            ft.Text(
                spans=[
                    ft.TextSpan(
                        "Tests",
                        style=ft.TextStyle(
                            color="#0064FF",
                            decoration_color="#0064FF",
                        ),
                        on_click=lambda e: e.page.go("/tests"),
                    )
                ],
                style=ft.TextThemeStyle.TITLE_MEDIUM,
            ),
            ft.Icon(
                ft.Icons.SCIENCE_OUTLINED,
                color="#0064FF",
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=0,
    )

    get_started = ft.Row(
        [
            ft.Markdown(
                "To get started, go to the",
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            ),
            tests_icon_link,
            ft.Markdown(
                "page and create your first test.",
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            ),
        ]
    )

    return ft.Column(
        [
            intro,
            features,
            get_started,
        ],
        spacing=50,
        expand=True,
    )
