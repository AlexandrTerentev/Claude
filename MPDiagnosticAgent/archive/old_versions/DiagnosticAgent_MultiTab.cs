using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using MissionPlanner;
using MissionPlanner.Plugin;
using MissionPlanner.GCSViews;

namespace MPDiagnosticAgent
{
    #region Localization / Локализация

    /// <summary>
    /// Localized strings - Russian with English in parentheses
    /// Локализованные строки - Русский с английским в скобках
    /// </summary>
    public static class Strings
    {
        // === UI ELEMENTS ===
        public const string Send = "Отправить (Send)";
        public const string Clear = "Очистить (Clear)";

        // === AGENT MESSAGES ===
        public const string AgentReady =
            "Агент диагностики готов!\n" +
            "Diagnostic Agent Ready!\n\n" +
            "Я могу помочь с:\n" +
            "I can help with:\n" +
            "- Диагностика моторов (Motor diagnostics)\n" +
            "- Калибровка (Calibration)\n" +
            "- Анализ логов (Log analysis)\n" +
            "- Решение проблем (Troubleshooting)\n\n" +
            "Задайте вопрос или напишите 'помощь' (help)";

        public const string NotConnected = "Не подключено (Not Connected)";
        public const string YouLabel = "Вы (You)";
        public const string AgentLabel = "Агент (Agent)";
        public const string ChatCleared = "Чат очищен. Чем могу помочь?\n\nChat cleared. How can I help?";

        // === HELP TEXT ===
        public const string HelpText =
            "ДОСТУПНЫЕ КОМАНДЫ (AVAILABLE COMMANDS):\n\n" +
            "БАЗОВЫЕ (BASIC):\n" +
            "  помощь (help)         - Показать эту справку / Show this help\n" +
            "  статус (status)       - Статус системы / System status\n\n" +
            "ДИАГНОСТИКА (DIAGNOSTICS):\n" +
            "  проверить ошибки (check errors)  - Найти ошибки в логах / Find errors in logs\n" +
            "  prearm                           - Проверить ошибки PreArm / Check PreArm errors\n" +
            "  показать логи (show logs)        - Последние записи лога / Recent log entries\n\n" +
            "ВОПРОСЫ (QUESTIONS):\n" +
            "  'Почему не крутятся моторы?' (Why won't motors spin?)\n" +
            "  'Как калибровать компас?' (How to calibrate compass?)\n" +
            "  'Моторы не работают' (Motors not working)\n\n" +
            "Вы можете задавать вопросы на русском или английском!\n" +
            "You can ask questions in Russian or English!";

        // === DIAGNOSTICS ===
        public const string MotorDiagnosisTitle =
            "ДИАГНОСТИКА МОТОРОВ/АРМИРОВАНИЯ\n" +
            "MOTOR/ARMING DIAGNOSIS:\n";

        public const string NoPrearmErrors =
            "PreArm ошибки не найдены.\n" +
            "No PreArm errors found.\n\n" +
            "ВОЗМОЖНЫЕ ПРИЧИНЫ (POSSIBLE CAUSES):\n" +
            "1. Дрон не подключен к Mission Planner / Drone not connected\n" +
            "2. Нет попыток армирования / No arming attempts logged\n" +
            "3. Все системы готовы / All systems ready\n\n" +
            "Попробуйте: 'показать логи' или 'show logs'";

        public const string FoundPrearmErrors = "Найдено PreArm ошибок: {0}\nFound PreArm errors: {0}\n";
        public const string RecommendedActions =
            "\nРЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ (RECOMMENDED ACTIONS):\n";

        public const string RcNotCalibrated =
            "! КОНТРОЛЛЕР RC НЕ ОТКАЛИБРОВАН (RC NOT CALIBRATED)\n\n" +
            "РЕШЕНИЕ (SOLUTION):\n" +
            "1. Перейти: Initial Setup > Mandatory Hardware > Radio Calibration\n" +
            "2. Включить передатчик RC / Turn on RC transmitter\n" +
            "3. Подвигать все стики / Move all sticks to extremes\n" +
            "4. Нажать 'Calibrate Radio'\n" +
            "5. Проверить ЗЕЛЕНЫЕ полосы / Verify GREEN bars\n" +
            "6. Нажать 'Click when Done'\n";

        public const string CompassNotCalibrated =
            "! НУЖНА КАЛИБРОВКА КОМПАСА (COMPASS CALIBRATION NEEDED)\n\n" +
            "РЕШЕНИЕ (SOLUTION):\n" +
            "1. Перейти: Initial Setup > Mandatory Hardware > Compass\n" +
            "2. Нажать 'Onboard Mag Calibration'\n" +
            "3. Выйти на улицу (подальше от металла / away from metal)\n" +
            "4. Медленно вращать по всем осям / Rotate slowly on all axes\n" +
            "5. Дождаться 'Calibration successful'\n";

        public const string AccelNotCalibrated =
            "! НУЖНА КАЛИБРОВКА АКСЕЛЕРОМЕТРА (ACCELEROMETER CALIBRATION NEEDED)\n\n" +
            "РЕШЕНИЕ (SOLUTION):\n" +
            "1. Перейти: Initial Setup > Mandatory Hardware > Accel Calibration\n" +
            "2. Следовать инструкциям на экране / Follow on-screen instructions\n" +
            "3. Размещать дрон в каждой позиции / Place drone in each orientation\n" +
            "4. Держать неподвижно / Keep still during measurement\n";

        public const string BatteryIssue =
            "! ПРОБЛЕМА С БАТАРЕЕЙ (BATTERY ISSUE)\n\n" +
            "ПРОВЕРИТЬ (CHECK):\n" +
            "1. Батарея подключена правильно? / Battery connected properly?\n" +
            "2. Напряжение достаточно? / Voltage sufficient?\n" +
            "3. Проверить параметры: Config/Full Parameter List\n";

        public const string GenericAdvice =
            "Для этой ошибки (For this error):\n" +
            "1. Внимательно прочитать сообщение / Read message carefully\n" +
            "2. Поиск: \"ArduPilot PreArm [текст ошибки]\"\n" +
            "3. Проверить документацию Mission Planner\n" +
            "4. Спросить на форуме ArduPilot при необходимости\n";

        // === CALIBRATION ===
        public const string CalibrationGuide =
            "РУКОВОДСТВО ПО КАЛИБРОВКЕ (CALIBRATION GUIDE):\n\n" +
            "КОМПАС (COMPASS):\n" +
            "  Initial Setup > Mandatory Hardware > Compass\n" +
            "  - Нажать 'Onboard Mag Calibration'\n" +
            "  - Выйти на улицу, вращать медленно / Go outside, rotate slowly\n\n" +
            "РАДИО RC (RADIO):\n" +
            "  Initial Setup > Mandatory Hardware > Radio Calibration\n" +
            "  - Двигать все стики до крайних позиций / Move all sticks to extremes\n" +
            "  - Проверить ЗЕЛЕНЫЕ полосы / Verify GREEN bars\n\n" +
            "АКСЕЛЕРОМЕТР (ACCELEROMETER):\n" +
            "  Initial Setup > Mandatory Hardware > Accel Calibration\n" +
            "  - Следовать инструкциям / Follow instructions\n" +
            "  - Размещать в каждой ориентации / Place in each orientation\n\n" +
            "ESC:\n" +
            "  Initial Setup > Optional Hardware > ESC Calibration\n" +
            "  - ОСТОРОЖНО: Моторы будут крутиться! / CAREFUL: Motors will spin!\n" +
            "  - Следовать инструкциям точно / Follow instructions exactly\n\n" +
            "Спросите: 'как калибровать [compass/radio/accel]?' для подробностей\n" +
            "Ask: 'how to calibrate [compass/radio/accel]?' for details";

        // === STATUS ===
        public const string StatusSummary = "СВОДКА СОСТОЯНИЯ СИСТЕМЫ (SYSTEM STATUS SUMMARY):\n";
        public const string NoErrors = "ОК - Ошибки не найдены (OK - No errors found)";
        public const string FoundErrors = "Найдено ошибок: {0} (Found errors: {0})\n";

        // === GENERAL ===
        public const string UnknownQuery =
            "Я понимаю, что вы спрашиваете о: \"{0}\"\n" +
            "I understand you're asking about: \"{0}\"\n\n" +
            "Я еще учусь! Сейчас я могу помочь с:\n" +
            "I'm still learning! Currently I can help with:\n" +
            "- Проблемы с моторами (Motor issues): \"почему не крутятся моторы?\"\n" +
            "- Калибровка (Calibration): \"как калибровать компас?\"\n" +
            "- Анализ логов (Log analysis): \"проверить ошибки\"\n\n" +
            "Напишите 'помощь' (help) для списка команд";
    }

    #endregion

    #region Data Models / Модели данных

    /// <summary>
    /// Log entry / Запись лога
    /// </summary>
    public class LogEntry
    {
        public string Timestamp { get; set; }
        public string Level { get; set; }
        public string Message { get; set; }
    }

    #endregion

    #region Main Plugin / Основной плагин

    /// <summary>
    /// Mission Planner Diagnostic Agent - Multi-Tab with Russian Support
    /// Агент диагностики Mission Planner - Мультивкладочный с поддержкой русского
    /// </summary>
    public class DiagnosticAgent : Plugin
    {
        #region Fields / Поля

        // UI Components - separate for each tab
        private RichTextBox chatBox;
        private TextBox inputBox;
        private Panel mainPanel;
        private Button sendBtn;

        // Shared chat history
        private List<ChatMessage> chatHistory = new List<ChatMessage>();

        // State
        private string currentTab = "DATA";
        private string logPath = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log";

        // Tab references
        private Control setupTab;
        private Control configTab;

        #endregion

        #region Chat Message Model

        private class ChatMessage
        {
            public string Sender { get; set; }
            public string Text { get; set; }
            public Color Color { get; set; }
            public DateTime Timestamp { get; set; }
        }

        #endregion

        #region Plugin Properties / Свойства плагина

        public override string Name => "Агент Диагностики (Diagnostic Agent)";
        public override string Version => "4.0";
        public override string Author => "Claude";

        #endregion

        #region Plugin Lifecycle / Жизненный цикл плагина

        public override bool Init()
        {
            try
            {
                // UTF-8 encoding setup for Russian support
                // Установка UTF-8 кодировки для поддержки русского языка
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

                // Set low loop rate (we don't need frequent updates)
                loopratehz = 0.1f;

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"DiagnosticAgent Init Error: {ex.Message}");
                return false;
            }
        }

        public override bool Loaded()
        {
            try
            {
                // Create main panel
                mainPanel = new Panel
                {
                    Dock = DockStyle.Right,
                    Width = 400,
                    BackColor = Color.FromArgb(240, 240, 240),
                    Padding = new Padding(5)
                };

                // Restore focus when panel becomes visible
                mainPanel.VisibleChanged += (s, e) =>
                {
                    if (mainPanel.Visible && inputBox != null && !inputBox.IsDisposed)
                    {
                        inputBox.BeginInvoke(new Action(() => inputBox.Focus()));
                    }
                };

                // Create chat history box
                chatBox = new RichTextBox
                {
                    Dock = DockStyle.Fill,
                    ReadOnly = true,
                    BackColor = Color.White,
                    Font = new Font("Consolas", 9),
                    BorderStyle = BorderStyle.FixedSingle
                };

                // Click on chatBox focuses input
                chatBox.Click += (s, e) => { if (!inputBox.IsDisposed) inputBox.Focus(); };

                // Create input panel
                var inputPanel = new Panel
                {
                    Dock = DockStyle.Bottom,
                    Height = 60,
                    BackColor = Color.FromArgb(240, 240, 240)
                };

                // Create input textbox
                inputBox = new TextBox
                {
                    Dock = DockStyle.Fill,
                    Font = new Font("Segoe UI", 10),
                    Multiline = true,
                    BackColor = Color.White,
                    ForeColor = Color.Black,
                    TabStop = true,
                    TabIndex = 0,
                    ImeMode = ImeMode.On  // Enable IME for international input
                };

                // NO KeyDown handler - let Russian input work naturally!

                // Create Send button with localized text
                sendBtn = new Button
                {
                    Dock = DockStyle.Right,
                    Width = 80,
                    Text = Strings.Send,
                    BackColor = Color.FromArgb(0, 120, 215),
                    ForeColor = Color.White,
                    FlatStyle = FlatStyle.Flat,
                    Cursor = Cursors.Hand
                };
                sendBtn.Click += (s, e) => SendMessage();

                // Assemble UI
                inputPanel.Controls.Add(inputBox);
                inputPanel.Controls.Add(sendBtn);
                mainPanel.Controls.Add(chatBox);
                mainPanel.Controls.Add(inputPanel);

                // Attach panel to DATA tab (always available)
                AttachPanelToTab(FlightData.instance, "DATA");

                // Try to find and attach to SETUP and CONFIG tabs
                TryAttachToAdditionalTabs();

                // Show welcome message
                AddMsg(Strings.AgentLabel, Strings.AgentReady, Color.Green);

                // Set initial focus
                inputBox.BeginInvoke(new Action(() =>
                {
                    System.Threading.Thread.Sleep(100);
                    if (!inputBox.IsDisposed)
                        inputBox.Focus();
                }));

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading Diagnostic Agent:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        public override bool Loop()
        {
            // Detect current tab
            DetectCurrentTab();

            // Restore focus to inputBox if panel is visible and active
            if (mainPanel != null && mainPanel.Visible && !mainPanel.IsDisposed)
            {
                if (inputBox != null && !inputBox.IsDisposed)
                {
                    // Only restore focus if nothing else has it within our panel
                    if (!inputBox.Focused && !chatBox.Focused && !sendBtn.Focused)
                    {
                        // Check if parent tab is visible
                        bool parentVisible = false;
                        if (currentTab == "DATA" && FlightData.instance?.Visible == true)
                            parentVisible = true;
                        else if (currentTab == "SETUP" && setupTab?.Visible == true)
                            parentVisible = true;
                        else if (currentTab == "CONFIG" && configTab?.Visible == true)
                            parentVisible = true;

                        if (parentVisible)
                        {
                            try
                            {
                                inputBox.Focus();
                            }
                            catch { }
                        }
                    }
                }
            }

            return true;
        }

        public override bool Exit()
        {
            try
            {
                if (mainPanel != null && !mainPanel.IsDisposed)
                    mainPanel.Dispose();
                return true;
            }
            catch
            {
                return false;
            }
        }

        #endregion

        #region UI Methods / Методы UI

        private void SendMessage()
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMsg(Strings.YouLabel, msg, Color.Blue);
            inputBox.Clear();
            inputBox.Focus();

            // Process query
            string response = ProcessQuery(msg);
            AddMsg(Strings.AgentLabel, response, Color.Green);
        }

        private void AddMsg(string sender, string text, Color color)
        {
            // Add to shared history
            chatHistory.Add(new ChatMessage
            {
                Sender = sender,
                Text = text,
                Color = color,
                Timestamp = DateTime.Now
            });

            // Update UI
            if (chatBox.InvokeRequired)
            {
                chatBox.Invoke(new Action(() => UpdateChatDisplay()));
                return;
            }

            UpdateChatDisplay();
        }

        private void UpdateChatDisplay()
        {
            if (chatBox == null || chatBox.IsDisposed) return;

            chatBox.Clear();

            foreach (var msg in chatHistory)
            {
                chatBox.SelectionStart = chatBox.TextLength;
                chatBox.SelectionColor = msg.Color;
                chatBox.SelectionFont = new Font(chatBox.Font, FontStyle.Bold);
                chatBox.AppendText($"[{msg.Timestamp:HH:mm:ss}] {msg.Sender}:\n");
                chatBox.SelectionColor = Color.Black;
                chatBox.SelectionFont = new Font(chatBox.Font, FontStyle.Regular);
                chatBox.AppendText($"{msg.Text}\n\n");
            }

            chatBox.SelectionStart = chatBox.TextLength;
            chatBox.ScrollToCaret();
        }

        #endregion

        #region Tab Management / Управление вкладками

        private void AttachPanelToTab(Control tab, string tabName)
        {
            if (tab == null) return;

            tab.BeginInvoke((MethodInvoker)delegate
            {
                if (!tab.Controls.Contains(mainPanel))
                {
                    tab.Controls.Add(mainPanel);
                    tab.Controls.SetChildIndex(mainPanel, 0);
                }
            });
        }

        private void TryAttachToAdditionalTabs()
        {
            try
            {
                // Try to find Setup tab
                var setupProperty = MainV2.instance.GetType().GetProperty("Setup");
                if (setupProperty != null)
                {
                    setupTab = setupProperty.GetValue(MainV2.instance) as Control;
                    if (setupTab != null)
                        AttachPanelToTab(setupTab, "SETUP");
                }

                // Try to find Config/ConfigTabs
                var configProperty = MainV2.instance.GetType().GetProperty("ConfigTabs");
                if (configProperty == null)
                    configProperty = MainV2.instance.GetType().GetProperty("Configuration");

                if (configProperty != null)
                {
                    configTab = configProperty.GetValue(MainV2.instance) as Control;
                    if (configTab != null)
                        AttachPanelToTab(configTab, "CONFIG");
                }
            }
            catch (Exception ex)
            {
                // If we can't find additional tabs, that's OK - we'll work on DATA tab only
                System.Diagnostics.Debug.WriteLine($"Could not attach to additional tabs: {ex.Message}");
            }
        }

        private void DetectCurrentTab()
        {
            if (FlightData.instance?.Visible == true)
                currentTab = "DATA";
            else if (setupTab?.Visible == true)
                currentTab = "SETUP";
            else if (configTab?.Visible == true)
                currentTab = "CONFIG";
        }

        #endregion

        #region Log Analysis / Анализ логов

        private List<string> ReadLogLines(int numLines = 100)
        {
            try
            {
                if (!File.Exists(logPath))
                    return new List<string>();

                // Read last N lines efficiently
                var lines = new List<string>();
                using (var reader = new StreamReader(logPath, Encoding.UTF8))
                {
                    string line;
                    var buffer = new Queue<string>(numLines);
                    while ((line = reader.ReadLine()) != null)
                    {
                        if (buffer.Count >= numLines)
                            buffer.Dequeue();
                        buffer.Enqueue(line);
                    }
                    lines.AddRange(buffer);
                }
                return lines;
            }
            catch
            {
                return new List<string>();
            }
        }

        private LogEntry ParseLogLine(string line)
        {
            try
            {
                // Parse format: "YYYY-MM-DD HH:mm:ss,ms LEVEL Logger - Message"
                var parts = line.Split(new[] { ' ' }, 4);
                if (parts.Length >= 4)
                {
                    return new LogEntry
                    {
                        Timestamp = parts[0] + " " + parts[1],
                        Level = parts[2],
                        Message = parts[3]
                    };
                }
            }
            catch { }

            return new LogEntry { Timestamp = "", Level = "", Message = line };
        }

        private List<LogEntry> FindPrearmErrors(int numLines = 300)
        {
            var errors = new List<LogEntry>();
            var lines = ReadLogLines(numLines);

            var regex = new Regex(@"PreArm:\s*(.+)$", RegexOptions.IgnoreCase);

            foreach (var line in lines)
            {
                var match = regex.Match(line);
                if (match.Success)
                {
                    var entry = ParseLogLine(line);
                    entry.Message = match.Groups[1].Value.Trim();
                    errors.Add(entry);
                }
            }

            return errors;
        }

        private List<LogEntry> FindErrors(int numLines = 300)
        {
            var errors = new List<LogEntry>();
            var lines = ReadLogLines(numLines);

            foreach (var line in lines)
            {
                if (line.Contains("ERROR") || line.Contains("CRITICAL"))
                {
                    errors.Add(ParseLogLine(line));
                }
            }

            return errors;
        }

        private string ExtractTimestamp(string line)
        {
            try
            {
                var parts = line.Split(new[] { ' ' }, 3);
                if (parts.Length >= 2)
                    return parts[0] + " " + parts[1];
            }
            catch { }
            return "";
        }

        #endregion

        #region Query Processing / Обработка запросов

        private string ProcessQuery(string userInput)
        {
            string query = userInput.ToLower().Trim();

            // Command detection - support both Russian and English
            if (query.Contains("помощь") || query.Contains("help") || query == "?")
                return ShowHelp();

            if (query.Contains("мотор") || query.Contains("motor") ||
                query.Contains("крутятся") || query.Contains("крутятся") ||
                query.Contains("spin") || query.Contains("arm") ||
                query.Contains("пропеллер") || query.Contains("propeller"))
                return DiagnoseMotors();

            if (query.Contains("калибр") || query.Contains("calibrat"))
                return ShowCalibrationInfo();

            if (query.Contains("лог") || query.Contains("log"))
                return ShowRecentLogs();

            if (query.Contains("ошибк") || query.Contains("error") ||
                query.Contains("проблем") || query.Contains("problem") ||
                query.Contains("issue"))
                return CheckErrors();

            if (query.Contains("prearm"))
                return CheckPrearm();

            if (query.Contains("статус") || query.Contains("status") ||
                query.Contains("сводка") || query.Contains("summary"))
                return GetStatusSummary();

            return GeneralResponse(userInput);
        }

        #endregion

        #region Diagnostic Methods / Методы диагностики

        private string DiagnoseMotors()
        {
            var prearmErrors = FindPrearmErrors(300);

            if (prearmErrors.Count == 0)
            {
                return Strings.NoPrearmErrors;
            }

            var response = new StringBuilder();
            response.AppendLine(Strings.MotorDiagnosisTitle);
            response.AppendLine(string.Format(Strings.FoundPrearmErrors, prearmErrors.Count));

            // Show unique errors (last 5)
            var uniqueErrors = prearmErrors
                .GroupBy(e => e.Message)
                .Select(g => g.First())
                .TakeLast(5);

            foreach (var err in uniqueErrors)
            {
                response.AppendLine($"✗ {err.Message}");
            }

            response.Append(new string('=', 50));
            response.Append(Strings.RecommendedActions);
            response.AppendLine(new string('=', 50));
            response.AppendLine();

            // Analyze error patterns and provide solutions
            string allErrorsText = string.Join(" ", prearmErrors.Select(e => e.Message.ToLower()));

            bool foundSolution = false;

            if (allErrorsText.Contains("rc not calibrated") || allErrorsText.Contains("rc3_min"))
            {
                response.AppendLine(Strings.RcNotCalibrated);
                foundSolution = true;
            }

            if (allErrorsText.Contains("compass") &&
                (allErrorsText.Contains("calibrat") || allErrorsText.Contains("inconsistent")))
            {
                response.AppendLine(Strings.CompassNotCalibrated);
                foundSolution = true;
            }

            if (allErrorsText.Contains("accel") && allErrorsText.Contains("calibrat"))
            {
                response.AppendLine(Strings.AccelNotCalibrated);
                foundSolution = true;
            }

            if (allErrorsText.Contains("battery") || allErrorsText.Contains("voltage"))
            {
                response.AppendLine(Strings.BatteryIssue);
                foundSolution = true;
            }

            if (!foundSolution)
            {
                response.AppendLine(Strings.GenericAdvice);
            }

            return response.ToString();
        }

        private string CheckPrearm()
        {
            var prearmErrors = FindPrearmErrors();

            if (prearmErrors.Count == 0)
            {
                return "OK - " + Strings.NoErrors;
            }

            var response = new StringBuilder();
            response.AppendLine(string.Format(Strings.FoundPrearmErrors, prearmErrors.Count));
            response.AppendLine();

            // Show last 5 unique errors
            var uniqueErrors = prearmErrors
                .GroupBy(e => e.Message)
                .Select(g => g.First())
                .TakeLast(5);

            foreach (var err in uniqueErrors)
            {
                string time = err.Timestamp.Length > 10 ? err.Timestamp.Substring(11) : err.Timestamp;
                response.AppendLine($"[{time}] {err.Message}");
            }

            return response.ToString();
        }

        private string CheckErrors()
        {
            var errors = FindErrors(300);

            if (errors.Count == 0)
            {
                return Strings.NoErrors;
            }

            var response = new StringBuilder();
            response.AppendLine(string.Format(Strings.FoundErrors, errors.Count));
            response.AppendLine();

            // Show last 5 errors
            foreach (var err in errors.TakeLast(5))
            {
                string time = err.Timestamp.Length > 10 ? err.Timestamp.Substring(11) : err.Timestamp;
                response.AppendLine($"[{time}] {err.Level}: {err.Message}");
            }

            return response.ToString();
        }

        private string ShowRecentLogs()
        {
            var lines = ReadLogLines(15);

            if (lines.Count == 0)
            {
                return "Файл лога не найден.\nLog file not found.\n\nПуть: " + logPath;
            }

            var response = new StringBuilder();
            response.AppendLine("ПОСЛЕДНИЕ ЗАПИСИ ЛОГА (RECENT LOG ENTRIES):\n");

            foreach (var line in lines)
            {
                response.AppendLine(line);
            }

            return response.ToString();
        }

        private string GetStatusSummary()
        {
            var response = new StringBuilder();
            response.AppendLine(Strings.StatusSummary);
            response.AppendLine();

            // Check connection
            try
            {
                var cs = MainV2.comPort.MAV.cs;
                response.AppendLine($"Режим (Mode): {cs.mode}");
                response.AppendLine($"Армирован (Armed): {cs.armed}");
                response.AppendLine($"Высота (Altitude): {cs.alt:F1}m");
                response.AppendLine($"Напряжение (Voltage): {cs.battery_voltage:F1}V");
                response.AppendLine($"GPS: {cs.gpsstatus}");
            }
            catch
            {
                response.AppendLine(Strings.NotConnected);
            }

            response.AppendLine();

            // Check for recent errors
            var prearmErrors = FindPrearmErrors(100);
            var logErrors = FindErrors(100);

            if (prearmErrors.Count > 0)
                response.AppendLine($"⚠ PreArm: {prearmErrors.Count} ошибок (errors)");

            if (logErrors.Count > 0)
                response.AppendLine($"⚠ Log: {logErrors.Count} ошибок (errors)");

            if (prearmErrors.Count == 0 && logErrors.Count == 0)
                response.AppendLine("✓ " + Strings.NoErrors);

            return response.ToString();
        }

        private string ShowHelp()
        {
            return Strings.HelpText;
        }

        private string ShowCalibrationInfo()
        {
            return Strings.CalibrationGuide;
        }

        private string GeneralResponse(string query)
        {
            return string.Format(Strings.UnknownQuery, query);
        }

        #endregion
    }

    #endregion
}
