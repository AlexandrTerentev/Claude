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
    /// Diagnostic Agent - Standalone Window (SUPER SIMPLE VERSION)
    /// </summary>
    public class DiagnosticWindow : Form
    {
        private RichTextBox chatBox;
        private TextBox inputBox;
        private Button sendBtn;
        private string logPath = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log";

        public DiagnosticWindow()
        {
            InitUI();
        }

        private void InitUI()
        {
            // Window settings
            this.Text = "🚁 Агент Диагностики / Diagnostic Agent";
            this.Size = new Size(600, 700);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.TopMost = true;  // Always on top
            this.BackColor = Color.FromArgb(45, 45, 48);
            this.ForeColor = Color.White;

            // Chat box
            chatBox = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = Color.FromArgb(30, 30, 30),
                ForeColor = Color.White,
                Font = new Font("Consolas", 10),
                Margin = new Padding(10)
            };

            // Input panel
            var inputPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 100,
                BackColor = Color.FromArgb(45, 45, 48),
                Padding = new Padding(10)
            };

            // Input box
            inputBox = new TextBox
            {
                Dock = DockStyle.Fill,
                Multiline = true,
                Font = new Font("Segoe UI", 11),
                BackColor = Color.FromArgb(60, 60, 60),
                ForeColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle
            };

            // Send button
            sendBtn = new Button
            {
                Dock = DockStyle.Bottom,
                Height = 40,
                Text = "📤 ОТПРАВИТЬ / SEND",
                BackColor = Color.FromArgb(0, 122, 204),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Cursor = Cursors.Hand
            };
            sendBtn.FlatAppearance.BorderSize = 0;
            sendBtn.Click += (s, e) => Send();

            // Assemble
            inputPanel.Controls.Add(inputBox);
            inputPanel.Controls.Add(sendBtn);
            this.Controls.Add(chatBox);
            this.Controls.Add(inputPanel);

            // Welcome
            AddMsg("🤖 Агент",
                "Привет! Я готов помогать.\n" +
                "Hello! I'm ready to help.\n\n" +
                "✅ МОЖНО ПИСАТЬ НА РУССКОМ!\n" +
                "✅ RUSSIAN INPUT WORKS!\n\n" +
                "Команды:\n" +
                "  помощь / help\n" +
                "  тест / test\n" +
                "  статус / status\n" +
                "  моторы / motors",
                Color.LimeGreen);
        }

        private void Send()
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMsg("👤 Вы", msg, Color.Cyan);
            inputBox.Clear();
            inputBox.Focus();

            string response = Process(msg);
            AddMsg("🤖 Агент", response, Color.LimeGreen);
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
            chatBox.AppendText($"\n[{DateTime.Now:HH:mm:ss}] {sender}:\n");
            chatBox.SelectionColor = Color.White;
            chatBox.SelectionFont = new Font(chatBox.Font, FontStyle.Regular);
            chatBox.AppendText($"{text}\n");
            chatBox.ScrollToCaret();
        }

        private string Process(string input)
        {
            string q = input.ToLower().Trim();

            if (q.Contains("помощь") || q.Contains("help"))
                return "📋 КОМАНДЫ:\n\n" +
                       "помощь / help - эта справка\n" +
                       "тест / test - проверка\n" +
                       "статус / status - статус дрона\n" +
                       "моторы / motors - диагностика\n" +
                       "ошибки / errors - найти ошибки\n" +
                       "логи / logs - показать логи\n" +
                       "prearm - проверка PreArm\n\n" +
                       "Пишите по-русски или по-английски!";

            if (q.Contains("тест") || q.Contains("test"))
                return "✅ РАБОТАЕТ! / WORKING!\n\n" +
                       "Русский: ДА ✓\n" +
                       "Russian: YES ✓\n\n" +
                       "Время: " + DateTime.Now.ToString("HH:mm:ss");

            if (q.Contains("статус") || q.Contains("status"))
            {
                try
                {
                    var cs = MainV2.comPort.MAV.cs;
                    return $"📊 СТАТУС:\n\n" +
                           $"Режим: {cs.mode}\n" +
                           $"Армирован: {cs.armed}\n" +
                           $"Высота: {cs.alt:F1}m\n" +
                           $"Напряжение: {cs.battery_voltage:F1}V\n" +
                           $"GPS: {cs.gpsstatus}";
                }
                catch
                {
                    return "❌ Дрон не подключен\n❌ Drone not connected";
                }
            }

            if (q.Contains("мотор") || q.Contains("motor"))
            {
                var errors = FindPreArm();
                if (errors.Count == 0)
                    return "✅ PreArm ошибок нет\n✅ No PreArm errors";

                var sb = new StringBuilder("⚠️  ОШИБКИ PreArm:\n\n");
                foreach (var err in errors.Take(5))
                    sb.AppendLine($"❌ {err}");
                return sb.ToString();
            }

            if (q.Contains("ошибк") || q.Contains("error"))
            {
                var errors = FindErrors();
                if (errors.Count == 0)
                    return "✅ Ошибок нет\n✅ No errors";

                var sb = new StringBuilder("⚠️  ОШИБКИ:\n\n");
                foreach (var err in errors.Take(5))
                    sb.AppendLine($"❌ {err}");
                return sb.ToString();
            }

            if (q.Contains("лог") || q.Contains("log"))
            {
                var logs = ReadLogs(10);
                if (logs.Count == 0)
                    return "❌ Логи не найдены";

                var sb = new StringBuilder("📋 ЛОГИ:\n\n");
                foreach (var line in logs)
                    sb.AppendLine(line);
                return sb.ToString();
            }

            if (q.Contains("prearm"))
            {
                var errors = FindPreArm();
                if (errors.Count == 0)
                    return "✅ PreArm: OK";

                var sb = new StringBuilder("⚠️  PreArm:\n\n");
                foreach (var err in errors.Take(5))
                    sb.AppendLine($"❌ {err}");
                return sb.ToString();
            }

            return $"Получено: \"{input}\"\n\n" +
                   "Напишите 'помощь' для списка команд.\n" +
                   "Type 'help' for command list.";
        }

        private List<string> ReadLogs(int n = 100)
        {
            try
            {
                if (!File.Exists(logPath)) return new List<string>();
                var lines = new List<string>();
                using (var r = new StreamReader(logPath, Encoding.UTF8))
                {
                    string line;
                    var q = new Queue<string>(n);
                    while ((line = r.ReadLine()) != null)
                    {
                        if (q.Count >= n) q.Dequeue();
                        q.Enqueue(line);
                    }
                    lines.AddRange(q);
                }
                return lines;
            }
            catch { return new List<string>(); }
        }

        private List<string> FindPreArm()
        {
            var errors = new List<string>();
            var lines = ReadLogs(300);
            var regex = new Regex(@"PreArm:\s*(.+)$", RegexOptions.IgnoreCase);
            foreach (var line in lines)
            {
                var m = regex.Match(line);
                if (m.Success) errors.Add(m.Groups[1].Value.Trim());
            }
            return errors;
        }

        private List<string> FindErrors()
        {
            var errors = new List<string>();
            var lines = ReadLogs(300);
            foreach (var line in lines)
            {
                if (line.Contains("ERROR") || line.Contains("CRITICAL"))
                    errors.Add(line);
            }
            return errors;
        }
    }

    /// <summary>
    /// Simple Plugin
    /// </summary>
    public class SimplePlugin : Plugin
    {
        private DiagnosticWindow window;

        public override string Name => "Агент (Simple)";
        public override string Version => "6.0";
        public override string Author => "Claude";

        public override bool Init()
        {
            try
            {
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
                return true;
            }
            catch { return false; }
        }

        public override bool Loaded()
        {
            try
            {
                // Just create and show window - NOTHING ELSE
                window = new DiagnosticWindow();
                window.Show();
                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
            catch { return false; }
        }
    }
}
