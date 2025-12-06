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

namespace MPDiagnosticAgent
{
    /// <summary>
    /// Standalone Diagnostic Agent Window - Always on Top
    /// Отдельное окно агента диагностики - Поверх всех окон
    /// </summary>
    public class DiagnosticAgentWindow : Form
    {
        private RichTextBox chatBox;
        private TextBox inputBox;
        private Button sendBtn;
        private Button clearBtn;
        private string logPath = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log";

        public DiagnosticAgentWindow()
        {
            InitializeUI();
        }

        private void InitializeUI()
        {
            // Window settings
            this.Text = "Агент Диагностики / Diagnostic Agent";
            this.Size = new Size(500, 600);
            this.StartPosition = FormStartPosition.Manual;
            this.Location = new Point(100, 100);
            this.TopMost = true;  // Always on top!
            this.FormBorderStyle = FormBorderStyle.Sizable;
            this.MinimumSize = new Size(400, 400);
            this.BackColor = Color.FromArgb(240, 240, 240);

            // Don't close the app when this form closes
            this.FormClosing += (s, e) =>
            {
                e.Cancel = true;
                this.Hide();
            };

            // Chat history box
            chatBox = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = Color.White,
                Font = new Font("Consolas", 9),
                BorderStyle = BorderStyle.FixedSingle,
                Margin = new Padding(5)
            };

            // Input panel at bottom
            var inputPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 80,
                BackColor = Color.FromArgb(240, 240, 240),
                Padding = new Padding(5)
            };

            // Input textbox - multiline for Russian input
            inputBox = new TextBox
            {
                Dock = DockStyle.Fill,
                Multiline = true,
                Font = new Font("Segoe UI", 10),
                BackColor = Color.White,
                ForeColor = Color.Black,
                BorderStyle = BorderStyle.FixedSingle,
                AcceptsReturn = true,
                AcceptsTab = false
            };

            // Buttons panel
            var btnPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 35,
                Padding = new Padding(0, 5, 0, 0)
            };

            // Send button
            sendBtn = new Button
            {
                Dock = DockStyle.Right,
                Width = 100,
                Text = "Отправить\n(Send)",
                BackColor = Color.FromArgb(0, 120, 215),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 8),
                Cursor = Cursors.Hand
            };
            sendBtn.Click += SendBtn_Click;

            // Clear button
            clearBtn = new Button
            {
                Dock = DockStyle.Right,
                Width = 100,
                Text = "Очистить\n(Clear)",
                BackColor = Color.Gray,
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 8),
                Cursor = Cursors.Hand
            };
            clearBtn.Click += (s, e) =>
            {
                chatBox.Clear();
                AddMessage("Агент", "Чат очищен. / Chat cleared.", Color.Green);
            };

            // Assemble UI
            btnPanel.Controls.Add(sendBtn);
            btnPanel.Controls.Add(clearBtn);
            inputPanel.Controls.Add(inputBox);
            inputPanel.Controls.Add(btnPanel);

            this.Controls.Add(chatBox);
            this.Controls.Add(inputPanel);

            // Welcome message
            AddMessage("Агент",
                "🚁 Агент Диагностики готов!\n" +
                "🚁 Diagnostic Agent ready!\n\n" +
                "✅ Можно писать на РУССКОМ!\n" +
                "✅ Russian input works!\n\n" +
                "Команды / Commands:\n" +
                "  помощь / help\n" +
                "  статус / status\n" +
                "  моторы / motors\n" +
                "  ошибки / errors\n\n" +
                "Окно всегда поверх других.\n" +
                "Window is always on top.",
                Color.Green);

            // Set focus to input
            this.Shown += (s, e) => inputBox.Focus();
        }

        private void SendBtn_Click(object sender, EventArgs e)
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMessage("Вы / You", msg, Color.Blue);
            inputBox.Clear();
            inputBox.Focus();

            string response = ProcessQuery(msg);
            AddMessage("Агент / Agent", response, Color.Green);
        }

        private void AddMessage(string sender, string text, Color color)
        {
            if (chatBox.InvokeRequired)
            {
                chatBox.Invoke(new Action(() => AddMessage(sender, text, color)));
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

        #region Query Processing

        private string ProcessQuery(string userInput)
        {
            string query = userInput.ToLower().Trim();

            if (query.Contains("помощь") || query.Contains("help") || query == "?")
                return GetHelp();

            if (query.Contains("статус") || query.Contains("status"))
                return GetStatus();

            if (query.Contains("мотор") || query.Contains("motor") ||
                query.Contains("крутятся") || query.Contains("spin"))
                return DiagnoseMotors();

            if (query.Contains("ошибк") || query.Contains("error"))
                return FindErrors();

            if (query.Contains("лог") || query.Contains("log"))
                return GetRecentLogs();

            if (query.Contains("prearm"))
                return CheckPreArm();

            if (query.Contains("калибр") || query.Contains("calibrat"))
                return GetCalibrationInfo();

            if (query.Contains("тест") || query.Contains("test"))
                return "✅ Агент работает! / Agent working!\n\n" +
                       "Русский язык: ДА ✓\n" +
                       "Russian input: YES ✓\n\n" +
                       "Время / Time: " + DateTime.Now.ToString("HH:mm:ss");

            return "Я понимаю: \"" + userInput + "\"\n" +
                   "I understand: \"" + userInput + "\"\n\n" +
                   "Напишите 'помощь' для списка команд.\n" +
                   "Type 'help' for command list.";
        }

        private string GetHelp()
        {
            return "КОМАНДЫ / COMMANDS:\n\n" +
                   "📋 БАЗОВЫЕ / BASIC:\n" +
                   "  помощь / help       - эта справка / this help\n" +
                   "  статус / status     - статус дрона / drone status\n" +
                   "  тест / test         - проверка работы / test agent\n\n" +
                   "🔧 ДИАГНОСТИКА / DIAGNOSTICS:\n" +
                   "  моторы / motors     - диагностика моторов / motor diagnosis\n" +
                   "  ошибки / errors     - поиск ошибок / find errors\n" +
                   "  логи / logs         - последние логи / recent logs\n" +
                   "  prearm              - проверка PreArm / check PreArm\n" +
                   "  калибровка / calibration - калибровки / calibrations\n\n" +
                   "💬 ВОПРОСЫ / QUESTIONS:\n" +
                   "  'Почему не крутятся моторы?'\n" +
                   "  'Why won't motors spin?'\n" +
                   "  'Проблема с батареей'\n" +
                   "  'Battery issue'\n\n" +
                   "Можно писать на русском или английском!\n" +
                   "You can write in Russian or English!";
        }

        private string GetStatus()
        {
            var result = new StringBuilder();
            result.AppendLine("СТАТУС СИСТЕМЫ / SYSTEM STATUS:\n");

            try
            {
                var cs = MainV2.comPort.MAV.cs;
                result.AppendLine($"📡 Подключено / Connected: ДА / YES");
                result.AppendLine($"🛸 Режим / Mode: {cs.mode}");
                result.AppendLine($"⚡ Армирован / Armed: {(cs.armed ? "ДА / YES" : "НЕТ / NO")}");
                result.AppendLine($"📏 Высота / Altitude: {cs.alt:F1}m");
                result.AppendLine($"🔋 Напряжение / Voltage: {cs.battery_voltage:F1}V");
                result.AppendLine($"🛰️ GPS: {cs.gpsstatus}");
            }
            catch
            {
                result.AppendLine("❌ Не подключено / Not connected");
                result.AppendLine("\nПодключите дрон к Mission Planner.");
                result.AppendLine("Connect drone to Mission Planner.");
            }

            return result.ToString();
        }

        private string DiagnoseMotors()
        {
            var prearmErrors = FindPrearmErrors();

            if (prearmErrors.Count == 0)
            {
                return "✅ PreArm ошибки не найдены.\n" +
                       "✅ No PreArm errors found.\n\n" +
                       "ВОЗМОЖНЫЕ ПРИЧИНЫ / POSSIBLE CAUSES:\n" +
                       "1. Дрон не подключен / Drone not connected\n" +
                       "2. Нет попыток армирования / No arming attempts\n" +
                       "3. Все системы готовы / All systems ready";
            }

            var result = new StringBuilder();
            result.AppendLine("🔧 ДИАГНОСТИКА МОТОРОВ / MOTOR DIAGNOSIS:\n");
            result.AppendLine($"Найдено ошибок / Found errors: {prearmErrors.Count}\n");

            var uniqueErrors = prearmErrors.GroupBy(e => e).Distinct().Take(5);
            foreach (var err in uniqueErrors)
            {
                result.AppendLine($"❌ {err}");
            }

            result.AppendLine("\n" + new string('=', 50));
            result.AppendLine("РЕКОМЕНДАЦИИ / RECOMMENDATIONS:");
            result.AppendLine(new string('=', 50) + "\n");

            string allErrors = string.Join(" ", prearmErrors).ToLower();

            if (allErrors.Contains("rc not calibrated") || allErrors.Contains("rc3_min"))
            {
                result.AppendLine("🎮 RC НЕ ОТКАЛИБРОВАН / RC NOT CALIBRATED\n");
                result.AppendLine("РЕШЕНИЕ / SOLUTION:");
                result.AppendLine("1. Initial Setup > Mandatory Hardware > Radio Calibration");
                result.AppendLine("2. Включить передатчик / Turn on transmitter");
                result.AppendLine("3. Двигать стики / Move sticks to extremes");
                result.AppendLine("4. Calibrate Radio");
                result.AppendLine("5. Проверить зеленые полосы / Check green bars\n");
            }

            if (allErrors.Contains("compass"))
            {
                result.AppendLine("🧭 КОМПАС НЕ ОТКАЛИБРОВАН / COMPASS NOT CALIBRATED\n");
                result.AppendLine("РЕШЕНИЕ / SOLUTION:");
                result.AppendLine("1. Initial Setup > Mandatory Hardware > Compass");
                result.AppendLine("2. Onboard Mag Calibration");
                result.AppendLine("3. Выйти на улицу / Go outside");
                result.AppendLine("4. Медленно вращать / Rotate slowly\n");
            }

            if (allErrors.Contains("accel"))
            {
                result.AppendLine("📐 АКСЕЛЕРОМЕТР / ACCELEROMETER\n");
                result.AppendLine("РЕШЕНИЕ / SOLUTION:");
                result.AppendLine("1. Initial Setup > Mandatory Hardware > Accel Calibration");
                result.AppendLine("2. Следовать инструкциям / Follow instructions\n");
            }

            return result.ToString();
        }

        private string FindErrors()
        {
            var errors = FindLogErrors();

            if (errors.Count == 0)
                return "✅ Ошибок не найдено в логах.\n✅ No errors found in logs.";

            var result = new StringBuilder();
            result.AppendLine($"⚠️  Найдено ошибок / Found errors: {errors.Count}\n");

            foreach (var err in errors.Take(10))
            {
                result.AppendLine($"❌ {err}");
            }

            return result.ToString();
        }

        private string GetRecentLogs()
        {
            var logs = ReadLogLines(15);

            if (logs.Count == 0)
                return "❌ Файл лога не найден.\n❌ Log file not found.\n\nПуть / Path: " + logPath;

            var result = new StringBuilder();
            result.AppendLine("📋 ПОСЛЕДНИЕ ЛОГИ / RECENT LOGS:\n");

            foreach (var line in logs)
            {
                result.AppendLine(line);
            }

            return result.ToString();
        }

        private string CheckPreArm()
        {
            var errors = FindPrearmErrors();

            if (errors.Count == 0)
                return "✅ PreArm: OK\n\nНет ошибок. / No errors.";

            var result = new StringBuilder();
            result.AppendLine($"⚠️  PreArm ошибки / PreArm errors: {errors.Count}\n");

            foreach (var err in errors.Distinct().Take(10))
            {
                result.AppendLine($"❌ {err}");
            }

            return result.ToString();
        }

        private string GetCalibrationInfo()
        {
            return "🛠️  КАЛИБРОВКА / CALIBRATION:\n\n" +
                   "🧭 КОМПАС / COMPASS:\n" +
                   "  Initial Setup > Mandatory Hardware > Compass\n" +
                   "  - Onboard Mag Calibration\n" +
                   "  - Вращать на улице / Rotate outside\n\n" +
                   "🎮 РАДИО / RADIO:\n" +
                   "  Initial Setup > Mandatory Hardware > Radio Calibration\n" +
                   "  - Двигать стики / Move sticks\n" +
                   "  - Зеленые полосы / Green bars\n\n" +
                   "📐 АКСЕЛЕРОМЕТР / ACCELEROMETER:\n" +
                   "  Initial Setup > Mandatory Hardware > Accel Calibration\n" +
                   "  - 6 позиций / 6 positions\n";
        }

        #endregion

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

        private List<string> FindPrearmErrors()
        {
            var errors = new List<string>();
            var lines = ReadLogLines(300);
            var regex = new Regex(@"PreArm:\s*(.+)$", RegexOptions.IgnoreCase);

            foreach (var line in lines)
            {
                var match = regex.Match(line);
                if (match.Success)
                {
                    errors.Add(match.Groups[1].Value.Trim());
                }
            }

            return errors;
        }

        private List<string> FindLogErrors()
        {
            var errors = new List<string>();
            var lines = ReadLogLines(300);

            foreach (var line in lines)
            {
                if (line.Contains("ERROR") || line.Contains("CRITICAL"))
                {
                    errors.Add(line);
                }
            }

            return errors;
        }

        #endregion
    }

    /// <summary>
    /// Plugin that creates standalone diagnostic window
    /// </summary>
    public class DiagnosticAgentPlugin : Plugin
    {
        private DiagnosticAgentWindow window;
        private ToolStripMenuItem menuItem;

        public override string Name => "Агент Диагностики (Standalone)";
        public override string Version => "5.0";
        public override string Author => "Claude";

        public override bool Init()
        {
            try
            {
                // UTF-8 support
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public override bool Loaded()
        {
            try
            {
                // Create window (but don't show yet)
                window = new DiagnosticAgentWindow();

                // Add menu item to open window
                menuItem = new ToolStripMenuItem
                {
                    Text = "Агент Диагностики / Diagnostic Agent",
                    ToolTipText = "Открыть окно агента диагностики (Открывается поверх всех окон)"
                };
                menuItem.Click += (s, e) =>
                {
                    if (window == null || window.IsDisposed)
                        window = new DiagnosticAgentWindow();

                    window.Show();
                    window.BringToFront();
                };

                // Add to Help menu
                var helpMenu = Host.MainMenu.Items.Cast<ToolStripItem>()
                    .FirstOrDefault(x => x.Text.Contains("Help") || x.Text.Contains("?"));

                if (helpMenu is ToolStripMenuItem helpMenuItem)
                {
                    helpMenuItem.DropDownItems.Add(new ToolStripSeparator());
                    helpMenuItem.DropDownItems.Add(menuItem);
                }
                else
                {
                    // Fallback: add to main menu bar
                    Host.MainMenu.Items.Add(menuItem);
                }

                // Show window immediately on startup
                window.Show();

                MessageBox.Show(
                    "Агент Диагностики загружен!\n\n" +
                    "Diagnostic Agent loaded!\n\n" +
                    "Окно открыто поверх всех окон.\n" +
                    "Window is open on top of all windows.\n\n" +
                    "Можно писать на РУССКОМ!\n" +
                    "Russian input works!",
                    "Агент Диагностики",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading agent:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        public override bool Loop()
        {
            return true;
        }

        public override bool Exit()
        {
            try
            {
                if (window != null && !window.IsDisposed)
                    window.Close();
                return true;
            }
            catch
            {
                return false;
            }
        }
    }
}
