import subprocess
import platform
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from core.assembly import Assembly, AppConfig
from core.automation import AutomationEngine


class AssemblyExecutor:
    """Executes assemblies - launches apps and runs their actions."""

    def __init__(self):
        self.automation = AutomationEngine()
        self._running = False

    def execute_assembly(
        self,
        assembly: Assembly,
        progress_callback: Callable[[str], None] | None = None,
        parallel: bool = True
    ) -> bool:
        """
        Execute an assembly - launch all apps and run their actions.

        Args:
            assembly: The assembly to execute
            progress_callback: Optional callback for progress updates
            parallel: If True, launch apps in parallel

        Returns:
            True if all apps executed successfully
        """
        self._running = True

        if not assembly.apps:
            if progress_callback:
                progress_callback("Сборка пуста - нет приложений для запуска")
            return False

        if progress_callback:
            progress_callback(f"Запуск сборки: {assembly.name}")

        if parallel:
            return self._execute_parallel(assembly, progress_callback)
        else:
            return self._execute_sequential(assembly, progress_callback)

    def _execute_sequential(
        self,
        assembly: Assembly,
        progress_callback: Callable[[str], None] | None
    ) -> bool:
        """Execute apps one by one."""
        all_success = True

        for app in assembly.apps:
            if not self._running:
                break

            success = self._execute_app(app, progress_callback)
            if not success:
                all_success = False

        return all_success

    def _execute_parallel(
        self,
        assembly: Assembly,
        progress_callback: Callable[[str], None] | None
    ) -> bool:
        """Execute apps in parallel."""
        all_success = True

        with ThreadPoolExecutor(max_workers=len(assembly.apps)) as executor:
            futures = {
                executor.submit(self._execute_app, app, progress_callback): app
                for app in assembly.apps
            }

            for future in as_completed(futures):
                if not self._running:
                    break

                app = futures[future]
                try:
                    success = future.result()
                    if not success:
                        all_success = False
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Ошибка {app.name}: {e}")
                    all_success = False

        return all_success

    def _execute_app(
        self,
        app: AppConfig,
        progress_callback: Callable[[str], None] | None
    ) -> bool:
        """Execute a single app - launch it and run its actions."""
        if progress_callback:
            progress_callback(f"Запуск: {app.name}")

        # Launch the application
        process = self._launch_app(app)
        if process is None:
            if progress_callback:
                progress_callback(f"Не удалось запустить: {app.name}")
            return False

        if progress_callback:
            progress_callback(f"Запущено: {app.name}")

        # Execute actions
        if app.actions:
            if progress_callback:
                progress_callback(f"Выполнение действий для: {app.name}")

            successful, total = self.automation.execute_actions(app.actions)

            if progress_callback:
                progress_callback(f"{app.name}: выполнено {successful}/{total} действий")

            return successful == total

        return True

    def _launch_app(self, app: AppConfig) -> subprocess.Popen | None:
        """Launch an application."""
        try:
            # Prepare command
            cmd = [app.executable_path]
            if app.arguments:
                cmd.extend(app.arguments.split())

            # Prepare working directory
            cwd = app.working_directory if app.working_directory else None

            # Platform-specific launch
            if platform.system() == "Windows":
                # Windows: use shell=True for .exe files
                process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Linux: direct execution
                process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

            return process

        except Exception as e:
            print(f"Error launching {app.name}: {e}")
            return None

    def stop(self) -> None:
        """Stop the current execution."""
        self._running = False
