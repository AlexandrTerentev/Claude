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

    public static class Strings
    {
        // UI ELEMENTS
        public const string Send = "Отправить (Send)";

        // AGENT MESSAGES
        public const string AgentReady =
            "Агент диагностики готов!\n" +
            "Diagnostic Agent Ready!\n\n" +
            "Я могу помочь с:\n" +
            "I can help with:\n" +
            "- Диагностика моторов (Motor diagnostics)\n" +
            "- Калибровка (Calibration)\n" +
            "- Анализ логов (Log analysis)\n\n" +
            "Для отправки используйте кнопку 'Отправить'\n" +
            "Use 'Send' button to submit (Russian input works!)";

        public const string YouLabel = "Вы (You)";
        public const string AgentLabel = "Агент (Agent)";

        // HELP TEXT
        public const string HelpText =
            "ДОСТУПНЫЕ КОМАНДЫ (AVAILABLE COMMANDS):\n\n" +
            "БАЗОВЫЕ (BASIC):\n" +
            "  помощь (help)         - Показать эту справку / Show this help\n" +
            "  статус (status)       - Статус системы / System status\n\n" +
            "ДИАГНОСТИКА (DIAGNOSTICS):\n" +
            "  проверить ошибки (check errors)  - Найти ошибки в логах\n" +
            "  prearm                           - Проверить ошибки PreArm\n" +
            "  показать логи (show logs)        - Последние записи лога\n\n" +
            "ВОПРОСЫ (QUESTIONS):\n" +
            "  'Почему не крутятся моторы?' (Why won't motors spin?)\n" +
            "  'Как калибровать компас?' (How to calibrate compass?)\n\n" +
            "Вы можете задавать вопросы на русском или английском!\n" +
            "You can ask questions in Russian or English!";

        public const string MotorDiagnosisTitle = "ДИАГНОСТИКА МОТОРОВ/АРМИРОВАНИЯ\nMOTOR/ARMING DIAGNOSIS:\n";

        public const string NoPrearmErrors =
            "PreArm ошибки не найдены.\n" +
            "No PreArm errors found.\n\n" +
            "ВОЗМОЖНЫЕ ПРИЧИНЫ (POSSIBLE CAUSES):\n" +
            "1. Дрон не подключен к Mission Planner / Drone not connected\n" +
            "2. Нет попыток армирования / No arming attempts logged\n" +
            "3. Все системы готовы / All systems ready\n\n" +
            "Попробуйте: 'показать логи' или 'show logs'";

        public const string FoundPrearmErrors = "Найдено PreArm ошибок: {0}\nFound PreArm errors: {0}\n";
        public const string RecommendedActions = "\nРЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ (RECOMMENDED ACTIONS):\n";

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
            "3. Проверить документацию Mission Planner\n";

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
            "  - Размещать в каждой ориентации / Place in each orientation\n";

        public const string NoErrors = "ОК - Ошибки не найдены (OK - No errors found)";
        public const string FoundErrors = "Найдено ошибок: {0} (Found errors: {0})\n";

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

    #region Data Models

    public class LogEntry
    {
        public string Timestamp { get; set; }
        public string Level { get; set; }
        public string Message { get; set; }
    }

    #endregion

    #region Main Plugin

    public class DiagnosticAgent : Plugin
    {
        private RichTextBox chatBox;
        private TextBox inputBox;
        private Panel mainPanel;
        private Button sendBtn;
        private string logPath = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log";

        public override string Name => "Агент Диагностики v4 (Diagnostic Agent v4)";
        public override string Version => "4.1";
        public override string Author => "Claude";

        public override bool Init()
        {
            try
            {
                // UTF-8 encoding setup for Russian support
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
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

                // Create chat history box
                chatBox = new RichTextBox
                {
                    Dock = DockStyle.Fill,
                    ReadOnly = true,
                    BackColor = Color.White,
                    Font = new Font("Consolas", 9),
                    BorderStyle = BorderStyle.FixedSingle
                };

                // Create input panel
                var inputPanel = new Panel
                {
                    Dock = DockStyle.Bottom,
                    Height = 70,
                    BackColor = Color.FromArgb(240, 240, 240),
                    Padding = new Padding(5)
                };

                // Create input textbox - IMPORTANT: No event handlers that block input!
                inputBox = new TextBox
                {
                    Dock = DockStyle.Fill,
                    Font = new Font("Segoe UI", 10),
                    Multiline = true,
                    BackColor = Color.White,
                    ForeColor = Color.Black,
                    AcceptsReturn = true,
                    AcceptsTab = false
                };

                // Create Send button
                sendBtn = new Button
                {
                    Dock = DockStyle.Bottom,
                    Height = 30,
                    Text = Strings.Send,
                    BackColor = Color.FromArgb(0, 120, 215),
                    ForeColor = Color.White,
                    FlatStyle = FlatStyle.Flat,
                    Cursor = Cursors.Hand
                };
                sendBtn.Click += SendButton_Click;

                // Assemble UI
                inputPanel.Controls.Add(inputBox);
                inputPanel.Controls.Add(sendBtn);
                mainPanel.Controls.Add(chatBox);
                mainPanel.Controls.Add(inputPanel);

                // Add to DATA tab only (simplified - no multi-tab for now)
                FlightData.instance.BeginInvoke((MethodInvoker)delegate
                {
                    FlightData.instance.Controls.Add(mainPanel);
                    FlightData.instance.Controls.SetChildIndex(mainPanel, 0);

                    // Focus handler when FlightData becomes visible
                    FlightData.instance.VisibleChanged += OnFlightDataVisibleChanged;
                });

                // Show welcome message
                AddMsg(Strings.AgentLabel, Strings.AgentReady, Color.Green);

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading Diagnostic Agent:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        private void OnFlightDataVisibleChanged(object sender, EventArgs e)
        {
            if (FlightData.instance.Visible && inputBox != null && !inputBox.IsDisposed)
            {
                inputBox.BeginInvoke((MethodInvoker)delegate
                {
                    try
                    {
                        inputBox.Focus();
                        inputBox.Select(inputBox.Text.Length, 0); // Move cursor to end
                    }
                    catch { }
                });
            }
        }

        public override bool Loop()
        {
            // Keep focus on inputBox when DATA tab is active
            try
            {
                if (FlightData.instance != null && FlightData.instance.Visible &&
                    inputBox != null && !inputBox.IsDisposed && !inputBox.Focused)
                {
                    // Only grab focus if user isn't clicking on something else
                    Control focused = GetFocusedControl(mainPanel);
                    if (focused == null || focused == mainPanel || focused == chatBox)
                    {
                        inputBox.Focus();
                    }
                }
            }
            catch { }

            return true;
        }

        private Control GetFocusedControl(Control container)
        {
            if (container == null) return null;
            foreach (Control c in container.Controls)
            {
                if (c.Focused) return c;
                Control focused = GetFocusedControl(c);
                if (focused != null) return focused;
            }
            return null;
        }

        public override bool Exit()
        {
            try
            {
                if (FlightData.instance != null)
                    FlightData.instance.VisibleChanged -= OnFlightDataVisibleChanged;

                if (mainPanel != null && !mainPanel.IsDisposed)
                    mainPanel.Dispose();
                return true;
            }
            catch
            {
                return false;
            }
        }

        private void SendButton_Click(object sender, EventArgs e)
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMsg(Strings.YouLabel, msg, Color.Blue);
            inputBox.Clear();
            inputBox.Focus();

            string response = ProcessQuery(msg);
            AddMsg(Strings.AgentLabel, response, Color.Green);
        }

        private void AddMsg(string sender, string text, Color color)
        {
            if (chatBox.InvokeRequired)
            {
                chatBox.Invoke(new Action(() => AddMsg(sender, text, color)));
                return;
            }

            chatBox.SelectionStart = chatBox.TextLength;
            chatBox.SelectionColor = color;
            chatBox.SelectionFont = new Font(chatBox.Font, FontStyle.Bold);
            chatBox.AppendText($"[{DateTime.Now:HH:mm:ss}] {sender}:\n");
            chatBox.SelectionColor = Color.Black;
            chatBox.SelectionFont = new Font(chatBox.Font, FontStyle.Regular);
            chatBox.AppendText($"{text}\n\n");
            chatBox.ScrollToCaret();
        }

        #region Log Analysis

        private List<string> ReadLogLines(int numLines = 100)
        {
            try
            {
                if (!File.Exists(logPath))
                    return new List<string>();

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

        #endregion

        #region Query Processing

        private string ProcessQuery(string userInput)
        {
            string query = userInput.ToLower().Trim();

            if (query.Contains("помощь") || query.Contains("help") || query == "?")
                return ShowHelp();

            if (query.Contains("мотор") || query.Contains("motor") ||
                query.Contains("крутятся") || query.Contains("spin") ||
                query.Contains("arm") || query.Contains("пропеллер"))
                return DiagnoseMotors();

            if (query.Contains("калибр") || query.Contains("calibrat"))
                return ShowCalibrationInfo();

            if (query.Contains("лог") || query.Contains("log"))
                return ShowRecentLogs();

            if (query.Contains("ошибк") || query.Contains("error") ||
                query.Contains("проблем") || query.Contains("problem"))
                return CheckErrors();

            if (query.Contains("prearm"))
                return CheckPrearm();

            if (query.Contains("статус") || query.Contains("status"))
                return GetStatusSummary();

            return GeneralResponse(userInput);
        }

        #endregion

        #region Diagnostic Methods

        private string DiagnoseMotors()
        {
            var prearmErrors = FindPrearmErrors(300);

            if (prearmErrors.Count == 0)
                return Strings.NoPrearmErrors;

            var response = new StringBuilder();
            response.AppendLine(Strings.MotorDiagnosisTitle);
            response.AppendLine(string.Format(Strings.FoundPrearmErrors, prearmErrors.Count));

            var uniqueErrors = prearmErrors.GroupBy(e => e.Message).Select(g => g.First()).TakeLast(5);
            foreach (var err in uniqueErrors)
                response.AppendLine($"✗ {err.Message}");

            response.Append(new string('=', 50));
            response.Append(Strings.RecommendedActions);
            response.AppendLine(new string('=', 50));
            response.AppendLine();

            string allErrorsText = string.Join(" ", prearmErrors.Select(e => e.Message.ToLower()));
            bool foundSolution = false;

            if (allErrorsText.Contains("rc not calibrated") || allErrorsText.Contains("rc3_min"))
            {
                response.AppendLine(Strings.RcNotCalibrated);
                foundSolution = true;
            }

            if (allErrorsText.Contains("compass") && (allErrorsText.Contains("calibrat") || allErrorsText.Contains("inconsistent")))
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
                response.AppendLine(Strings.GenericAdvice);

            return response.ToString();
        }

        private string CheckPrearm()
        {
            var prearmErrors = FindPrearmErrors();
            if (prearmErrors.Count == 0)
                return "OK - " + Strings.NoErrors;

            var response = new StringBuilder();
            response.AppendLine(string.Format(Strings.FoundPrearmErrors, prearmErrors.Count));
            response.AppendLine();

            var uniqueErrors = prearmErrors.GroupBy(e => e.Message).Select(g => g.First()).TakeLast(5);
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
                return Strings.NoErrors;

            var response = new StringBuilder();
            response.AppendLine(string.Format(Strings.FoundErrors, errors.Count));
            response.AppendLine();

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
                return "Файл лога не найден.\nLog file not found.\n\nПуть: " + logPath;

            var response = new StringBuilder();
            response.AppendLine("ПОСЛЕДНИЕ ЗАПИСИ ЛОГА (RECENT LOG ENTRIES):\n");
            foreach (var line in lines)
                response.AppendLine(line);

            return response.ToString();
        }

        private string GetStatusSummary()
        {
            var response = new StringBuilder();
            response.AppendLine("СВОДКА СОСТОЯНИЯ (STATUS SUMMARY):\n");

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
                response.AppendLine("Не подключено (Not Connected)");
            }

            response.AppendLine();

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
