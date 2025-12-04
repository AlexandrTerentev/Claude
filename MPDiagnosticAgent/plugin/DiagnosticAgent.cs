using System;
using System.Drawing;
using System.Windows.Forms;
using System.IO;
using MissionPlanner;
using MissionPlanner.Plugin;
using MissionPlanner.GCSViews;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;

namespace MPDiagnosticAgent
{
    /// <summary>
    /// Chat Panel UI Component
    /// Панель чата для взаимодействия с AI агентом
    /// </summary>
    public class ChatPanel : UserControl
    {
        private RichTextBox chatHistory;
        private TextBox inputBox;
        private Button sendButton;
        private Button clearButton;
        private Panel inputPanel;

        public event Action<string> OnUserMessage;

        public ChatPanel()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            // Размеры и цвета
            this.Size = new Size(400, 600);
            this.BackColor = Color.FromArgb(240, 240, 240);
            this.Padding = new Padding(5);

            // Chat history (scrollable text box)
            chatHistory = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = Color.White,
                Font = new Font("Consolas", 9),
                BorderStyle = BorderStyle.FixedSingle,
                DetectUrls = false
            };

            // Input panel (внизу)
            inputPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 80,
                Padding = new Padding(5),
                BackColor = Color.FromArgb(240, 240, 240)
            };

            // Input textbox
            inputBox = new TextBox
            {
                Dock = DockStyle.Top,
                Multiline = true,
                Height = 40,
                Font = new Font("Segoe UI", 9),
                BorderStyle = BorderStyle.FixedSingle
            };
            inputBox.KeyDown += InputBox_KeyDown;

            // Buttons panel
            var buttonPanel = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 30,
                Padding = new Padding(0, 5, 0, 0)
            };

            // Send button
            sendButton = new Button
            {
                Dock = DockStyle.Right,
                Width = 80,
                Text = "Send",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(0, 120, 215),
                ForeColor = Color.White,
                Cursor = Cursors.Hand
            };
            sendButton.Click += SendButton_Click;

            // Clear button
            clearButton = new Button
            {
                Dock = DockStyle.Right,
                Width = 80,
                Text = "Clear",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(100, 100, 100),
                ForeColor = Color.White,
                Cursor = Cursors.Hand,
                Margin = new Padding(0, 0, 5, 0)
            };
            clearButton.Click += ClearButton_Click;

            // Assemble UI
            buttonPanel.Controls.Add(sendButton);
            buttonPanel.Controls.Add(clearButton);

            inputPanel.Controls.Add(buttonPanel);
            inputPanel.Controls.Add(inputBox);

            this.Controls.Add(chatHistory);
            this.Controls.Add(inputPanel);

            // Welcome message
            AddAgentMessage("Hello! I'm your Mission Planner diagnostic assistant.\n\n" +
                          "I can help you with:\n" +
                          "- Diagnosing motor issues\n" +
                          "- Calibration guidance\n" +
                          "- Analyzing flight data\n" +
                          "- Troubleshooting problems\n\n" +
                          "What can I help you with today?");
        }

        private void InputBox_KeyDown(object sender, KeyEventArgs e)
        {
            // Send on Ctrl+Enter
            if (e.Control && e.KeyCode == Keys.Enter)
            {
                SendButton_Click(sender, e);
                e.Handled = true;
                e.SuppressKeyPress = true;
            }
        }

        private void SendButton_Click(object sender, EventArgs e)
        {
            string message = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(message)) return;

            // Show user message
            AddUserMessage(message);
            inputBox.Clear();
            inputBox.Focus();

            // Trigger event for plugin to handle
            OnUserMessage?.Invoke(message);
        }

        private void ClearButton_Click(object sender, EventArgs e)
        {
            chatHistory.Clear();
            AddAgentMessage("Chat cleared. How can I help you?");
        }

        public void AddUserMessage(string message)
        {
            AppendMessage("User", message, Color.FromArgb(0, 102, 204), FontStyle.Bold);
        }

        public void AddAgentMessage(string message)
        {
            AppendMessage("Agent", message, Color.FromArgb(0, 153, 0), FontStyle.Bold);
        }

        public void AddErrorMessage(string message)
        {
            AppendMessage("Error", message, Color.FromArgb(204, 0, 0), FontStyle.Bold);
        }

        public void AddSystemMessage(string message)
        {
            AppendMessage("System", message, Color.FromArgb(128, 128, 128), FontStyle.Italic);
        }

        private void AppendMessage(string sender, string message, Color senderColor, FontStyle senderStyle)
        {
            if (chatHistory.InvokeRequired)
            {
                chatHistory.Invoke(new Action(() => AppendMessage(sender, message, senderColor, senderStyle)));
                return;
            }

            chatHistory.SelectionStart = chatHistory.TextLength;
            chatHistory.SelectionLength = 0;

            // Timestamp
            chatHistory.SelectionColor = Color.Gray;
            chatHistory.SelectionFont = new Font(chatHistory.Font.FontFamily, 8, FontStyle.Italic);
            chatHistory.AppendText($"[{DateTime.Now:HH:mm:ss}] ");

            // Sender
            chatHistory.SelectionColor = senderColor;
            chatHistory.SelectionFont = new Font(chatHistory.Font, senderStyle);
            chatHistory.AppendText($"{sender}: ");

            // Message
            chatHistory.SelectionColor = Color.Black;
            chatHistory.SelectionFont = new Font(chatHistory.Font, FontStyle.Regular);
            chatHistory.AppendText($"{message}\n\n");

            // Scroll to bottom
            chatHistory.SelectionStart = chatHistory.TextLength;
            chatHistory.ScrollToCaret();
        }
    }

    /// <summary>
    /// Mission Planner Plugin
    /// </summary>
    public class Plugin : MissionPlanner.Plugin.Plugin
    {
        private ChatPanel chatPanel;
        private ScriptEngine pythonEngine;
        private ScriptScope pythonScope;
        private string projectPath;

        public override string Name => "Diagnostic Agent";
        public override string Version => "1.0.0";
        public override string Author => "Claude + User";

        public override bool Init()
        {
            try
            {
                // Определить путь к проекту
                // Используем фиксированный путь для Linux
                projectPath = "/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent";

                // Проверить существование папки
                if (!Directory.Exists(projectPath))
                {
                    System.Windows.Forms.MessageBox.Show(
                        $"Project folder not found:\n{projectPath}\n\n" +
                        "Please ensure the project is in the correct location.",
                        "Diagnostic Agent Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return false;
                }

                // Инициализировать IronPython движок
                pythonEngine = Python.CreateEngine();
                pythonScope = pythonEngine.CreateScope();

                // Добавить путь к Python модулям
                var searchPaths = pythonEngine.GetSearchPaths();
                searchPaths.Add(Path.Combine(projectPath, "engine"));
                pythonEngine.SetSearchPaths(searchPaths);

                return true;
            }
            catch (Exception ex)
            {
                System.Windows.Forms.MessageBox.Show(
                    $"Failed to initialize Diagnostic Agent:\n{ex.Message}",
                    "Diagnostic Agent Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return false;
            }
        }

        public override bool Loaded()
        {
            try
            {
                // Создать UI панель
                chatPanel = new ChatPanel();
                chatPanel.Dock = DockStyle.Right;
                chatPanel.Width = 400;
                chatPanel.OnUserMessage += HandleUserMessage;

                // Добавить панель к FlightData (справа)
                FlightData.instance.BeginInvoke((MethodInvoker)delegate
                {
                    if (!FlightData.instance.Controls.Contains(chatPanel))
                    {
                        FlightData.instance.Controls.Add(chatPanel);
                        FlightData.instance.Controls.SetChildIndex(chatPanel, 0);
                    }
                });

                // Загрузить Python модуль
                string agentCorePath = Path.Combine(projectPath, "engine", "agent_core.py");

                if (!File.Exists(agentCorePath))
                {
                    chatPanel.AddErrorMessage($"Python module not found:\n{agentCorePath}");
                    return false;
                }

                pythonEngine.ExecuteFile(agentCorePath, pythonScope);
                chatPanel.AddSystemMessage("Python engine initialized successfully!");

                return true;
            }
            catch (Exception ex)
            {
                if (chatPanel != null)
                {
                    chatPanel.AddErrorMessage($"Failed to load plugin:\n{ex.Message}");
                }
                return false;
            }
        }

        private void HandleUserMessage(string message)
        {
            try
            {
                // Показать статус
                chatPanel.AddSystemMessage("Processing your request...");

                // Установить переменные для Python
                pythonScope.SetVariable("user_input", message);

                // Вызвать Python функцию
                pythonEngine.Execute("response = process_query(user_input)", pythonScope);

                // Получить ответ
                dynamic response = pythonScope.GetVariable("response");
                string responseStr = response.ToString();

                // Показать ответ
                chatPanel.AddAgentMessage(responseStr);
            }
            catch (Exception ex)
            {
                chatPanel.AddErrorMessage($"Error processing request:\n{ex.Message}\n\n" +
                                        "Stack trace:\n" + ex.StackTrace);
            }
        }

        public override bool Loop()
        {
            // Периодические обновления (если нужны в будущем)
            return true;
        }

        public override bool Exit()
        {
            try
            {
                // Очистка ресурсов
                if (pythonEngine != null)
                {
                    pythonEngine.Runtime.Shutdown();
                }

                if (chatPanel != null)
                {
                    chatPanel.Dispose();
                }

                return true;
            }
            catch
            {
                return false;
            }
        }
    }
}
