using System;
using System.Drawing;
using System.Windows.Forms;
using System.IO;
using System.Text;
using MissionPlanner;
using MissionPlanner.Plugin;
using MissionPlanner.GCSViews;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;

namespace MPDiagnosticAgent
{
    public class DiagnosticAgentPython : Plugin
    {
        private RichTextBox chatBox;
        private TextBox inputBox;
        private Panel mainPanel;
        private ScriptEngine pyEngine;
        private ScriptScope pyScope;
        private bool pythonReady = false;

        public override string Name => "Diagnostic Agent (Python)";
        public override string Version => "3.0";
        public override string Author => "Claude";

        public override bool Init()
        {
            try
            {
                // Установка UTF-8 кодировки для поддержки русского языка
                Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

                // Initialize Python
                pyEngine = Python.CreateEngine();
                pyScope = pyEngine.CreateScope();

                string projectPath = "/home/user_1/Desktop/No_problem/Claude/MPDiagnosticAgent";
                if (Directory.Exists(projectPath))
                {
                    var searchPaths = pyEngine.GetSearchPaths();
                    searchPaths.Add(projectPath);
                    pyEngine.SetSearchPaths(searchPaths);

                    string engineFile = Path.Combine(projectPath, "core", "diagnostic_engine.py");
                    if (File.Exists(engineFile))
                    {
                        // Установка кодировки Python для корректной работы с UTF-8
                        pyEngine.Execute("import sys; sys.setdefaultencoding('utf-8') if hasattr(sys, 'setdefaultencoding') else None", pyScope);
                        pyEngine.ExecuteFile(engineFile, pyScope);
                        pythonReady = true;
                    }
                }

                loopratehz = 0.1f;
                return true;
            }
            catch (Exception ex)
            {
                pythonReady = false;
                // Логируем ошибку для диагностики
                System.Diagnostics.Debug.WriteLine($"Python init error: {ex.Message}");
                return true; // Continue anyway
            }
        }

        public override bool Loaded()
        {
            try
            {
                mainPanel = new Panel
                {
                    Dock = DockStyle.Right,
                    Width = 400,
                    BackColor = Color.FromArgb(240, 240, 240),
                    Padding = new Padding(5)
                };

                // Восстанавливать фокус при показе панели
                mainPanel.VisibleChanged += (s, e) =>
                {
                    if (mainPanel.Visible && inputBox != null)
                    {
                        inputBox.BeginInvoke(new Action(() => inputBox.Focus()));
                    }
                };

                chatBox = new RichTextBox
                {
                    Dock = DockStyle.Fill,
                    ReadOnly = true,
                    BackColor = Color.White,
                    Font = new Font("Consolas", 9)
                };

                // При клике на chatBox или mainPanel переводить фокус на inputBox
                chatBox.Click += (s, e) => { if (!inputBox.IsDisposed) inputBox.Focus(); };
                mainPanel.Click += (s, e) => { if (inputBox != null && !inputBox.IsDisposed) inputBox.Focus(); };

                var inputPanel = new Panel
                {
                    Dock = DockStyle.Bottom,
                    Height = 60
                };

                inputBox = new TextBox
                {
                    Dock = DockStyle.Fill,
                    Font = new Font("Segoe UI", 10),
                    Multiline = true,
                    BackColor = Color.White,  // Белый фон
                    ForeColor = Color.Black,  // Черный текст
                    TabStop = true,
                    TabIndex = 0
                };
                // Без обработки Enter - теперь работает русский язык
                // Для отправки используйте кнопку Send

                var sendBtn = new Button
                {
                    Dock = DockStyle.Right,
                    Width = 70,
                    Text = "Send",
                    BackColor = Color.FromArgb(0, 120, 215),
                    ForeColor = Color.White
                };
                sendBtn.Click += (s, e) => SendMessage();

                inputPanel.Controls.Add(inputBox);
                inputPanel.Controls.Add(sendBtn);
                mainPanel.Controls.Add(chatBox);
                mainPanel.Controls.Add(inputPanel);

                // Добавляем панель на вкладку DATA
                FlightData.instance.BeginInvoke((MethodInvoker)delegate
                {
                    FlightData.instance.Controls.Add(mainPanel);
                    FlightData.instance.Controls.SetChildIndex(mainPanel, 0);

                    // Обработчик для восстановления фокуса при показе вкладки
                    FlightData.instance.VisibleChanged += (s, e) =>
                    {
                        if (FlightData.instance.Visible && inputBox != null && !inputBox.IsDisposed)
                        {
                            inputBox.BeginInvoke(new Action(() =>
                            {
                                if (!inputBox.IsDisposed)
                                    inputBox.Focus();
                            }));
                        }
                    };

                    // Устанавливаем фокус после добавления
                    inputBox.BeginInvoke(new Action(() =>
                    {
                        System.Threading.Thread.Sleep(100);
                        if (!inputBox.IsDisposed)
                            inputBox.Focus();
                    }));
                });

                string startMsg = pythonReady
                    ? "Python AI Agent готов!\n\nЗадайте любой вопрос о дроне.\n\nНапишите сообщение и нажмите кнопку Send."
                    : "Basic Agent готов (Python недоступен)\n\nНапишите 'help' для списка команд.\n\nНажмите кнопку Send для отправки.";
                AddMsg("Agent", startMsg, Color.Green);

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}");
                return false;
            }
        }

        private void SendMessage()
        {
            string msg = inputBox.Text.Trim();
            if (string.IsNullOrEmpty(msg)) return;

            AddMsg("You", msg, Color.Blue);
            inputBox.Clear();
            inputBox.Focus();

            string response;
            if (pythonReady)
            {
                try
                {
                    pyScope.SetVariable("user_input", msg);
                    pyEngine.Execute("response = process_query(user_input)", pyScope);
                    response = pyScope.GetVariable("response").ToString();
                }
                catch (Exception ex)
                {
                    response = $"Python Error: {ex.Message}";
                }
            }
            else
            {
                response = ProcessBasic(msg);
            }

            AddMsg("Agent", response, Color.Green);
        }

        private string ProcessBasic(string cmd)
        {
            cmd = cmd.ToLower();
            if (cmd.Contains("help"))
                return "Commands: help, status, test, logs\n\nOr ask questions about your drone!";
            if (cmd.Contains("status"))
            {
                try
                {
                    var cs = MainV2.comPort.MAV.cs;
                    return $"Mode: {cs.mode}\nArmed: {cs.armed}\nAlt: {cs.alt:F1}m";
                }
                catch
                {
                    return "Not connected";
                }
            }
            if (cmd.Contains("test"))
                return "Agent working!\nPython: " + (pythonReady ? "Ready" : "Not available");

            return $"Echo: {cmd}\n\n(Python not available, showing echo)";
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

        public override bool Loop()
        {
            // Если панель видима и на переднем плане, но фокус потерян - восстановить
            if (mainPanel != null && mainPanel.Visible && mainPanel.Parent != null)
            {
                if (mainPanel.Parent.Visible && !inputBox.Focused && !chatBox.Focused)
                {
                    // Проверяем, активна ли вкладка FlightData
                    if (MainV2.instance.FlightData != null && MainV2.instance.FlightData.Visible)
                    {
                        // Не переводим фокус агрессивно, только если пользователь кликнул в область панели
                        // это предотвратит постоянный захват фокуса
                    }
                }
            }
            return true;
        }

        public override bool Exit()
        {
            try
            {
                if (pyEngine != null) pyEngine.Runtime.Shutdown();
                if (mainPanel != null) mainPanel.Dispose();
            }
            catch { }
            return true;
        }
    }
}
