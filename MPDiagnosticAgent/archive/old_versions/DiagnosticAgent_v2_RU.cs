using System;
using System.Drawing;
using System.Windows.Forms;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using MissionPlanner;
using MissionPlanner.Plugin;
using MissionPlanner.GCSViews;
using MissionPlanner.Utilities;

namespace MPDiagnosticAgent
{
    /// <summary>
    /// Панель чата для диагностического агента
    /// </summary>
    public class ChatPanel : UserControl
    {
        private RichTextBox chatHistory;
        private TextBox inputBox;
        private Button sendButton;
        private Button clearButton;

        public event Action<string> OnUserMessage;

        public ChatPanel()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Size = new Size(450, 600);
            this.BackColor = Color.FromArgb(240, 240, 240);
            this.Padding = new Padding(5);

            // История чата
            chatHistory = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = Color.White,
                Font = new Font("Consolas", 9),
                BorderStyle = BorderStyle.FixedSingle
            };

            // Панель ввода
            var inputPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 80,
                BackColor = Color.FromArgb(240, 240, 240)
            };

            inputBox = new TextBox
            {
                Dock = DockStyle.Top,
                Multiline = true,
                Height = 40,
                Font = new Font("Segoe UI", 9)
            };

            // УБРАНО: KeyDown обработчик блокирует русский ввод!
            // Используйте кнопку "Отправить" для отправки сообщения
            // KeyDown handler REMOVED - it blocks Russian input!
            // Use "Send" button to submit messages

            var buttonPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 30
            };

            sendButton = new Button
            {
                Dock = DockStyle.Right,
                Width = 80,
                Text = "Отправить",
                BackColor = Color.FromArgb(0, 120, 215),
                ForeColor = Color.White
            };
            sendButton.Click += (s, e) => SendMessage();

            clearButton = new Button
            {
                Dock = DockStyle.Right,
                Width = 80,
                Text = "Очистить",
                BackColor = Color.Gray,
                ForeColor = Color.White
            };
            clearButton.Click += (s, e) => ClearChat();

            buttonPanel.Controls.Add(sendButton);
            buttonPanel.Controls.Add(clearButton);
            inputPanel.Controls.Add(buttonPanel);
            inputPanel.Controls.Add(inputBox);
            this.Controls.Add(chatHistory);
            this.Controls.Add(inputPanel);

            AddMessage("Агент",
                "Привет! Диагностический агент готов.\n" +
                "Hello! Diagnostic agent ready.\n\n" +
                "Можно писать на русском! (Russian input works!)\n\n" +
                "Команды / Commands:\n" +
                "  помощь / help - справка\n" +
                "  статус / status - состояние дрона\n\n" +
                "Используйте кнопку 'Отправить' для отправки.\n" +
                "Use 'Send' button to submit.",
                Color.Green);
        }

        private void SendMessage()
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMessage("Вы", msg, Color.Blue);
            inputBox.Clear();
            inputBox.Focus();
            OnUserMessage?.Invoke(msg);
        }

        private void ClearChat()
        {
            chatHistory.Clear();
            AddMessage("Агент", "Чат очищен.", Color.Green);
        }

        public void AddMessage(string sender, string text, Color color)
        {
            if (chatHistory.InvokeRequired)
            {
                chatHistory.Invoke(new Action(() => AddMessage(sender, text, color)));
                return;
            }

            chatHistory.SelectionStart = chatHistory.TextLength;
            chatHistory.SelectionColor = color;
            chatHistory.SelectionFont = new Font(chatHistory.Font, FontStyle.Bold);
            chatHistory.AppendText($"[{DateTime.Now:HH:mm:ss}] {sender}:\n");
            chatHistory.SelectionColor = Color.Black;
            chatHistory.SelectionFont = new Font(chatHistory.Font, FontStyle.Regular);
            chatHistory.AppendText($"{text}\n\n");
            chatHistory.ScrollToCaret();
        }

        public void FocusInput()
        {
            inputBox.Focus();
        }
    }

    /// <summary>
    /// Диагностический агент - плагин для Mission Planner
    /// </summary>
    public class DiagnosticAgentV2 : Plugin
    {
        private ChatPanel chatPanel;
        private Form chatForm;
        private ToolStripMenuItem menuItem;

        public override string Name => "Диагностический Агент";
        public override string Version => "2.5";
        public override string Author => "Claude";

        public override bool Init()
        {
            loopratehz = 0.1f;
            return true;
        }

        public override bool Loaded()
        {
            try
            {
                // Создаем панель
                chatPanel = new ChatPanel();
                chatPanel.Dock = DockStyle.Right;
                chatPanel.Width = 450;
                chatPanel.OnUserMessage += HandleMessage;

                // Добавляем на вкладку DATA
                FlightData.instance.BeginInvoke((MethodInvoker)delegate
                {
                    FlightData.instance.Controls.Add(chatPanel);
                    FlightData.instance.Controls.SetChildIndex(chatPanel, 0);
                    chatPanel.FocusInput();
                });

                // Добавляем пункт меню для доступа из других вкладок
                AddMenuItem();

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка загрузки: {ex.Message}", "Диагностический Агент", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        private void AddMenuItem()
        {
            try
            {
                ToolStripMenuItem helpMenu = null;
                foreach (ToolStripMenuItem item in Host.FDMenuMap.Items)
                {
                    if (item.Text.Contains("Help") || item.Text.Contains("Помощь") || item.Text == "?")
                    {
                        helpMenu = item;
                        break;
                    }
                }

                if (helpMenu == null)
                {
                    helpMenu = new ToolStripMenuItem("Помощь");
                    Host.FDMenuMap.Items.Add(helpMenu);
                }

                menuItem = new ToolStripMenuItem("🤖 Диагностический Агент");
                menuItem.Click += (s, e) => ShowChatWindow();
                helpMenu.DropDownItems.Add(menuItem);
            }
            catch { }
        }

        private void ShowChatWindow()
        {
            if (chatForm == null || chatForm.IsDisposed)
            {
                chatForm = new Form
                {
                    Text = "Диагностический Агент",
                    Width = 500,
                    Height = 700,
                    StartPosition = FormStartPosition.CenterScreen,
                    Icon = SystemIcons.Question
                };

                var panel = new ChatPanel();
                panel.Dock = DockStyle.Fill;
                panel.OnUserMessage += HandleMessage;
                chatForm.Controls.Add(panel);
                chatForm.Show();
            }
            else
            {
                chatForm.BringToFront();
                chatForm.Focus();
            }
        }

        private void HandleMessage(string msg)
        {
            string response = ProcessCommand(msg);
            chatPanel.AddMessage("Агент", response, Color.Green);

            // Если окно открыто, тоже обновляем
            if (chatForm != null && !chatForm.IsDisposed)
            {
                var panel = chatForm.Controls[0] as ChatPanel;
                if (panel != null)
                    panel.AddMessage("Агент", response, Color.Green);
            }
        }

        private string ProcessCommand(string cmd)
        {
            string original = cmd;
            cmd = cmd.ToLower().Trim();

            // Команда help
            if (cmd == "help" || cmd == "помощь" || cmd == "?")
            {
                return @"📋 ДОСТУПНЫЕ КОМАНДЫ:

🔧 БАЗОВЫЕ:
  help, ? - показать эту справку
  status - статус подключения к дрону
  info - подробная информация о системе
  params - показать ключевые параметры
  logs - последние записи логов
  errors - поиск ошибок в логах
  test - тест работы агента

🚁 ДИАГНОСТИКА:
  motors - диагностика моторов
  prearm - проверка PreArm ошибок
  calibration - статус калибровок
  gps - информация о GPS
  battery - информация о батарее
  rc - статус RC пульта

💡 СОВЕТ: Можете задавать вопросы естественным языком!
Например: 'почему не крутятся винты?'";
            }

            // Команда status
            else if (cmd == "status" || cmd == "статус")
            {
                return GetStatus();
            }

            // Команда info
            else if (cmd == "info" || cmd == "инфо")
            {
                return GetDetailedInfo();
            }

            // Команда params
            else if (cmd == "params" || cmd == "параметры")
            {
                return GetKeyParameters();
            }

            // Команда logs
            else if (cmd == "logs" || cmd == "логи")
            {
                return GetRecentLogs();
            }

            // Команда errors
            else if (cmd == "errors" || cmd == "ошибки")
            {
                return FindErrors();
            }

            // Команда test
            else if (cmd == "test" || cmd == "тест")
            {
                return "✅ Агент работает нормально!\n\nВерсия: " + Version + "\nВремя: " + DateTime.Now.ToString("HH:mm:ss");
            }

            // Команда motors
            else if (cmd == "motors" || cmd == "моторы" || cmd.Contains("мотор") || cmd.Contains("motor"))
            {
                return DiagnoseMotors();
            }

            // Команда prearm
            else if (cmd == "prearm" || cmd.Contains("prearm"))
            {
                return CheckPreArm();
            }

            // Команда calibration
            else if (cmd == "calibration" || cmd == "калибровка" || cmd.Contains("калибр"))
            {
                return CheckCalibration();
            }

            // Команда gps
            else if (cmd == "gps")
            {
                return GetGPSInfo();
            }

            // Команда battery
            else if (cmd == "battery" || cmd == "батарея" || cmd == "аккумулятор")
            {
                return GetBatteryInfo();
            }

            // Команда rc
            else if (cmd == "rc" || cmd == "пульт" || cmd.Contains("radio"))
            {
                return GetRCInfo();
            }

            // Естественный язык - моторы
            else if (cmd.Contains("вин") || cmd.Contains("крут") || cmd.Contains("spin") || cmd.Contains("arm"))
            {
                return DiagnoseMotors();
            }

            // Неизвестная команда
            else
            {
                return $"❓ Неизвестная команда: '{original}'\n\nВведите 'help' для списка команд.";
            }
        }

        private string GetStatus()
        {
            try
            {
                if (MainV2.comPort.BaseStream.IsOpen)
                {
                    var cs = MainV2.comPort.MAV.cs;
                    return $@"✅ ПОДКЛЮЧЕНО К ДРОНУ

Режим: {cs.mode}
Готовность: {(cs.armed ? "⚡ ARMED" : "🔒 DISARMED")}
Высота: {cs.alt:F1} м
Скорость: {cs.groundspeed:F1} м/с
Батарея: {cs.battery_voltage:F1}V ({cs.battery_remaining}%)
Спутников: {cs.satcount}";
                }
                return "❌ НЕ ПОДКЛЮЧЕНО\n\nДрон не подключен к Mission Planner.";
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка получения статуса: {ex.Message}";
            }
        }

        private string GetDetailedInfo()
        {
            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                    return "❌ Дрон не подключен.";

                var cs = MainV2.comPort.MAV.cs;
                return $@"📊 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ

🔌 ПОДКЛЮЧЕНИЕ:
  Тип: {cs.firmware}
  Порт: {MainV2.comPort.BaseStream.PortName}
  Baud: {MainV2.comPort.BaseStream.BaudRate}

🚁 СОСТОЯНИЕ:
  Режим: {cs.mode}
  Статус: {(cs.armed ? "ARMED" : "DISARMED")}
  GPS Fix: {cs.gpsstatus}
  Спутники: {cs.satcount}

📍 ПОЗИЦИЯ:
  Широта: {cs.lat:F7}
  Долгота: {cs.lng:F7}
  Высота: {cs.alt:F1} м
  Скорость: {cs.groundspeed:F1} м/с

🔋 ПИТАНИЕ:
  Напряжение: {cs.battery_voltage:F2}V
  Ток: {cs.current:F1}A
  Заряд: {cs.battery_remaining}%
  Израсходовано: {cs.battery_usedmah} mAh

🧭 ОРИЕНТАЦИЯ:
  Roll: {cs.roll:F1}°
  Pitch: {cs.pitch:F1}°
  Yaw: {cs.yaw:F1}°";
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка: {ex.Message}";
            }
        }

        private string GetKeyParameters()
        {
            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                    return "❌ Дрон не подключен.";

                var param = MainV2.comPort.MAV.param;
                var result = "🔧 КЛЮЧЕВЫЕ ПАРАМЕТРЫ:\n\n";

                // RC параметры
                result += "📡 RC CHANNELS:\n";
                for (int i = 1; i <= 4; i++)
                {
                    if (param.ContainsKey($"RC{i}_MIN") && param.ContainsKey($"RC{i}_MAX"))
                    {
                        result += $"  RC{i}: {param[$"RC{i}_MIN"]} - {param[$"RC{i}_MAX"]}\n";
                    }
                }

                result += "\n🧭 COMPASS:\n";
                if (param.ContainsKey("COMPASS_ENABLE"))
                    result += $"  Enabled: {param["COMPASS_ENABLE"]}\n";

                result += "\n⚡ ARMING:\n";
                if (param.ContainsKey("ARMING_CHECK"))
                    result += $"  Checks: {param["ARMING_CHECK"]}\n";

                return result;
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка получения параметров: {ex.Message}";
            }
        }

        private string GetRecentLogs()
        {
            try
            {
                string logFile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                                               "missionplanner", "Mission Planner", "MissionPlanner.log");

                if (!File.Exists(logFile))
                    return "❌ Файл логов не найден.";

                var lines = File.ReadAllLines(logFile).Reverse().Take(10).Reverse();
                return "📄 ПОСЛЕДНИЕ ЗАПИСИ ЛОГОВ:\n\n" + string.Join("\n", lines);
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка чтения логов: {ex.Message}";
            }
        }

        private string FindErrors()
        {
            try
            {
                string logFile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                                               "missionplanner", "Mission Planner", "MissionPlanner.log");

                if (!File.Exists(logFile))
                    return "❌ Файл логов не найден.";

                var lines = File.ReadAllLines(logFile);
                var errors = lines.Where(l => l.Contains("ERROR") || l.Contains("WARN") || l.Contains("CRITICAL"))
                                  .Reverse().Take(10).Reverse();

                if (!errors.Any())
                    return "✅ Ошибок в логах не найдено.";

                return "⚠ НАЙДЕННЫЕ ОШИБКИ:\n\n" + string.Join("\n", errors);
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка поиска ошибок: {ex.Message}";
            }
        }

        private string DiagnoseMotors()
        {
            var result = "🚁 ДИАГНОСТИКА МОТОРОВ\n\n";

            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                {
                    result += "❌ Дрон не подключен.\n\n";
                    result += "ОБЩИЕ РЕКОМЕНДАЦИИ:\n";
                    result += "1. Подключите дрон к Mission Planner\n";
                    result += "2. Проверьте команду 'prearm' для поиска ошибок\n";
                    return result;
                }

                var cs = MainV2.comPort.MAV.cs;
                result += $"Статус: {(cs.armed ? "⚡ ARMED" : "🔒 DISARMED")}\n\n";

                result += "ТИПИЧНЫЕ ПРОБЛЕМЫ:\n\n";
                result += "1. 📡 RC НЕ ОТКАЛИБРОВАН\n";
                result += "   Решение: Initial Setup > Radio Calibration\n\n";

                result += "2. 🔴 SAFETY SWITCH НЕ НАЖАТ\n";
                result += "   Решение: Нажмите красную кнопку на GPS модуле\n\n";

                result += "3. ❌ PREARM ПРОВЕРКИ\n";
                result += "   Решение: Введите команду 'prearm' для деталей\n\n";

                result += "4. ⚡ ESC НЕ ОТКАЛИБРОВАНЫ\n";
                result += "   Решение: Optional Hardware > ESC Calibration\n\n";

                result += "5. 🧭 COMPASS НЕ ОТКАЛИБРОВАН\n";
                result += "   Решение: Mandatory Hardware > Compass\n\n";

                result += "💡 Введите 'calibration' для проверки калибровок";

                return result;
            }
            catch (Exception ex)
            {
                return result + $"\n⚠ Ошибка: {ex.Message}";
            }
        }

        private string CheckPreArm()
        {
            try
            {
                string logFile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                                               "missionplanner", "Mission Planner", "MissionPlanner.log");

                if (!File.Exists(logFile))
                    return "❌ Файл логов не найден.";

                var lines = File.ReadAllLines(logFile);
                var prearmErrors = lines.Where(l => l.Contains("PreArm:")).Reverse().Take(10).Reverse();

                if (!prearmErrors.Any())
                    return "✅ PreArm ошибок не найдено в логах.";

                return "⚠ НАЙДЕННЫЕ PREARM ОШИБКИ:\n\n" + string.Join("\n", prearmErrors);
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка: {ex.Message}";
            }
        }

        private string CheckCalibration()
        {
            return @"🔧 СТАТУС КАЛИБРОВОК

Проверьте следующие калибровки:

📡 RADIO (RC):
  Initial Setup > Mandatory Hardware > Radio Calibration
  ✓ Все каналы должны показывать GREEN
  ✓ MIN ~1000, MAX ~2000

🧭 COMPASS:
  Initial Setup > Mandatory Hardware > Compass
  ✓ Калибровка на открытом воздухе
  ✓ Вдали от металлических объектов

📐 ACCELEROMETER:
  Initial Setup > Mandatory Hardware > Accel Calibration
  ✓ Поместите дрон во все 6 позиций
  ✓ Держите неподвижно при измерении

⚡ ESC:
  Optional Hardware > ESC Calibration
  ⚠ ВНИМАНИЕ: Снимите пропеллеры!

Введите 'params' чтобы проверить текущие значения.";
        }

        private string GetGPSInfo()
        {
            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                    return "❌ Дрон не подключен.";

                var cs = MainV2.comPort.MAV.cs;
                return $@"📡 GPS ИНФОРМАЦИЯ

Статус: {cs.gpsstatus}
Спутников: {cs.satcount}
HDOP: {cs.gpshdop:F1}

Координаты:
  Широта: {cs.lat:F7}
  Долгота: {cs.lng:F7}
  Высота: {cs.alt:F1} м

Скорость:
  Земная: {cs.groundspeed:F1} м/с
  Курс: {cs.groundcourse:F1}°

{(cs.satcount < 6 ? "⚠ МАЛО СПУТНИКОВ! Выйдите на открытое место." : "✅ GPS работает нормально.")}";
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка: {ex.Message}";
            }
        }

        private string GetBatteryInfo()
        {
            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                    return "❌ Дрон не подключен.";

                var cs = MainV2.comPort.MAV.cs;
                return $@"🔋 БАТАРЕЯ

Напряжение: {cs.battery_voltage:F2}V
Ток: {cs.current:F1}A
Заряд: {cs.battery_remaining}%
Израсходовано: {cs.battery_usedmah} mAh

{(cs.battery_voltage < 3.5 * 3 ? "⚠ НИЗКОЕ НАПРЯЖЕНИЕ!" : "✅ Напряжение в норме.")}
{(cs.battery_remaining < 20 ? "⚠ НИЗКИЙ ЗАРЯД!" : "")}";
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка: {ex.Message}";
            }
        }

        private string GetRCInfo()
        {
            try
            {
                if (!MainV2.comPort.BaseStream.IsOpen)
                    return "❌ Дрон не подключен.";

                var cs = MainV2.comPort.MAV.cs;
                return $@"📡 RC ПУЛЬТ

CH1 (Roll): {cs.ch1in}
CH2 (Pitch): {cs.ch2in}
CH3 (Throttle): {cs.ch3in}
CH4 (Yaw): {cs.ch4in}
CH5: {cs.ch5in}
CH6: {cs.ch6in}

RSSI: {cs.rssi}

Введите 'params' для проверки калибровки.";
            }
            catch (Exception ex)
            {
                return $"⚠ Ошибка: {ex.Message}";
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
                if (menuItem != null)
                {
                    var parent = menuItem.GetCurrentParent();
                    if (parent != null)
                        parent.Items.Remove(menuItem);
                }

                if (chatPanel != null)
                    chatPanel.Dispose();

                if (chatForm != null && !chatForm.IsDisposed)
                    chatForm.Close();
            }
            catch { }
            return true;
        }
    }
}
