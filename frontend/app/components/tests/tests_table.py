import flet as ft
import asyncio
import json
import csv
import io
from app.models import Test
from app.store import STORE
from app.utils.date import format_date
from app.utils.routing import Router
from app.utils.query_api import download_test_data
from app.env import SDK_TOKEN, get_marimo_url, get_lake_query_ui_url

from ..base import PLACEHOLDER, ConfirmationDialog
from .status_badge import TestStatusBadge
from urllib.parse import quote


class TestsTable:
    def __init__(self, tests: list[Test], router: Router):
        self._tests = tests
        self._router = router

    def _on_delete(self, e: ft.ControlEvent):
        test_id = e.control.data

        def on_submit():
            STORE.delete_test(test_id=test_id)
            self._router.refresh(e.page)

        dialog = ConfirmationDialog(
            title=ft.Text("Please confirm"),
            content=ft.Text(f'Are you sure you want to delete Test "{test_id}"?'),
            on_confirm=on_submit,
        )
        e.page.open(dialog.render())

    def _on_download(self, e: ft.ControlEvent):
        """Handle download button click."""
        test_id = e.control.data
        print(f"Download clicked for test_id: {test_id}")
        
        # Find the test object to get campaign_id and environment_id
        test = next((t for t in self._tests if t.test_id == test_id), None)
        if not test:
            print(f"Test not found: {test_id}")
            return
            
        print(f"Downloading data for test: campaign_id={test.campaign_id}, environment_id={test.environment_id}, test_id={test.test_id}")
        
        # Run the async download in a new thread
        asyncio.run(self._download_data(e, test))
    
    async def _download_data(self, e: ft.ControlEvent, test: Test):
        """Async method to download test data."""
        test_id = test.test_id
        
        try:
            # Show loading indicator
            e.control.disabled = True
            e.control.icon = ft.Icons.HOURGLASS_EMPTY
            e.page.update()
            
            # Make the API call
            data = await download_test_data(
                campaign_id=test.campaign_id,
                environment_id=test.environment_id,
                test_id=test.test_id
            )
            print(f"Data received: {type(data)}, length: {len(str(data))}")
            print(f"First 200 chars of data: {data[:200]}...")
            
            # The data is coming as a string, let's check if it's JSON or CSV
            import json
            import base64
            
            try:
                # Try to parse as JSON first
                parsed_data = json.loads(data)
                print(f"Parsed JSON data: {type(parsed_data)}")
                
                if isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], dict):
                    # List of dictionaries - convert to CSV
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=parsed_data[0].keys())
                    writer.writeheader()
                    writer.writerows(parsed_data)
                    csv_content = output.getvalue()
                elif isinstance(parsed_data, dict):
                    # Single dictionary - convert to CSV with one row
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=parsed_data.keys())
                    writer.writeheader()
                    writer.writerow(parsed_data)
                    csv_content = output.getvalue()
                else:
                    # Use the data as is
                    csv_content = str(parsed_data)
            except json.JSONDecodeError:
                # Not JSON, use as-is (might already be CSV)
                print("Data is not JSON, using as-is")
                csv_content = data
            
            # TODO this is not used
            filename = f"test_data_{test_id}.csv"
            
            # Create a data URL and trigger download
            # Encode the CSV content to base64
            encoded_data = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
            
            # Create a download link
            download_url = f"data:text/csv;charset=utf-8;base64,{encoded_data}"
            
            # Use Flet's launch_url to trigger the download
            e.page.launch_url(download_url)
            
            e.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Downloaded data for test {test_id}"),
                action="OK",
            )
            e.page.snack_bar.open = True
            e.page.update()
            
        except Exception as ex:
            # Show error message
            print(f"Error downloading data: {type(ex).__name__}: {str(ex)}")
            import traceback
            traceback.print_exc()
            
            e.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error downloading data: {str(ex)}"),
                action="OK",
                bgcolor=ft.Colors.ERROR,
            )
            e.page.snack_bar.open = True
            e.page.update()
        finally:
            # Reset button state
            e.control.disabled = False
            e.control.icon = ft.Icons.DOWNLOAD
            e.page.update()

    def render(self) -> ft.Control:
        if not self._tests:
            return ft.Row(
                [ft.Text("No entries", theme_style=ft.TextThemeStyle.TITLE_SMALL)]
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Test ID", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Environment ID", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Campaign ID", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Sample ID", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Operator", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Start date", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("End date", weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("", weight=ft.FontWeight.W_600)),
            ],
            expand=True,
            horizontal_lines=ft.BorderSide(1, ft.Colors.OUTLINE),
            show_bottom_border=False,
        )

        for test in self._tests:
            actions_menu_button = ft.PopupMenuButton(
                icon_color="#3d89ff",  # Set the three dots color
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.REMOVE_RED_EYE, color="#3d89ff"),
                                ft.Text("View"),
                            ]
                        ),
                        data=test.test_id,
                        on_click=lambda e: e.page.go(f"/tests/{e.control.data}"),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.EDIT, color=ft.Colors.GREEN),
                                ft.Text("Edit"),
                            ]
                        ),
                        data=test.test_id,
                        on_click=lambda e: e.page.go(
                            f"/tests/{e.control.data}/edit",
                        ),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED),
                                ft.Text("Delete"),
                            ]
                        ),
                        data=test.test_id,
                        on_click=self._on_delete,
                    ),
                ],
                tooltip="Actions",
            )

            from app.theme import theme_manager
            
            # Construct Marimo dashboard URL with parameters
            import urllib.parse
            
            marimo_base_url = get_marimo_url()
            marimo_params = {
                'sdk_token': SDK_TOKEN,
                'campaign_id': test.campaign_id,
                'test_id': test.test_id,
                'environment_id': test.environment_id
            }
            marimo_url = f"{marimo_base_url}?{urllib.parse.urlencode(marimo_params)}"
            
            lake_query_url = get_lake_query_ui_url()
            sql = quote(f"SELECT * FROM config-enriched-data\nWHERE campaign_id = '{test.campaign_id}'\nAND environment_id = '{test.environment_id}'\nAND test_id = '{test.test_id}'\nLIMIT 100")
            lake_sql_editor_querystring = f"?token={SDK_TOKEN}&sql={sql}&autorun=true" if test.test_id else f"?token={SDK_TOKEN}"
            lake_sql_editor_url = f"{lake_query_url}{lake_sql_editor_querystring}"

            sql_button = ft.IconButton(
                icon=ft.Icons.STORAGE,
                data=test.test_id,
                icon_color=theme_manager.colors.active_icon if SDK_TOKEN else theme_manager.colors.inactive_icon,
                url_target=ft.UrlTarget.BLANK,
                url=lake_sql_editor_url if SDK_TOKEN else None,
                disabled=not SDK_TOKEN,
                tooltip="Go to Data Query" if SDK_TOKEN else "SDK token not configured",
            )

            dashboard_button = ft.IconButton(
                icon=ft.Icons.AREA_CHART,
                data=test.test_id,
                icon_color=theme_manager.colors.active_icon if SDK_TOKEN else theme_manager.colors.inactive_icon,
                url_target=ft.UrlTarget.BLANK,
                url=marimo_url if SDK_TOKEN else None,
                disabled=not SDK_TOKEN,
                tooltip="Go to Notebook" if SDK_TOKEN else "SDK token not configured",
            )
            download_button = ft.IconButton(
                icon=ft.Icons.DOWNLOAD,
                data=test.test_id,
                icon_color=theme_manager.colors.active_icon,
                tooltip="Download test data",
                disabled=False,
                on_click=self._on_download,
            )
            # Wrap test_id cell into a GestureDetector to make the cursor look like
            # a usual link
            test_id_cell = ft.DataCell(
                ft.GestureDetector(
                    content=ft.Text(
                        test.test_id,
                        style=ft.TextStyle(
                            color=theme_manager.colors.link_color,
                            decoration=ft.TextDecoration.UNDERLINE,
                            decoration_color=theme_manager.colors.link_color,
                        ),
                        tooltip=f'View test "{test.test_id}"',
                    ),
                    data=test.test_id,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda e: e.page.go(f"/tests/{e.control.data}"),
                )
            )
            actions = ft.Row(
                controls=[
                    # actions_menu_button,
                    sql_button,
                    dashboard_button,
                    download_button,
                ],
                tight=True,
            )
            table.rows.append(
                ft.DataRow(
                    cells=[
                        test_id_cell,
                        ft.DataCell(TestStatusBadge(status=test.status).render()),
                        ft.DataCell(ft.Text(test.environment_id, selectable=True)),
                        ft.DataCell(ft.Text(test.campaign_id, selectable=True)),
                        ft.DataCell(ft.Text(test.sample_id, selectable=True)),
                        ft.DataCell(ft.Text(test.operator, selectable=True)),
                        ft.DataCell(
                            ft.Text(
                                format_date(test.start),
                                selectable=True,
                            )
                            if test.start
                            else PLACEHOLDER,
                        ),
                        ft.DataCell(
                            ft.Text(
                                format_date(test.end),
                                selectable=True,
                            )
                            if test.end
                            else PLACEHOLDER,
                        ),
                        ft.DataCell(actions),
                    ],
                ),
            )
        return table
