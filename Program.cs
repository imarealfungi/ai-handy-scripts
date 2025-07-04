using Buttplug;
using Buttplug.Client;
using System;
using System.IO;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;

namespace handyman
{
    class HandyServer
    {
        private ButtplugClient client;
        private ButtplugClientDevice device;
        private bool isConnected = false;
        private bool isPaused = true;
        private double speedMultiplier = 1.0;

        static async Task Main(string[] args)
        {
            var server = new HandyServer();
            await server.Start();
        }

        public async Task Start()
        {
            Console.WriteLine("Starting Handy Web Server...");

            // Connect to Intiface
            await ConnectToIntiface();

            // Start HTTP server
            var listener = new HttpListener();
            listener.Prefixes.Add("http://localhost:8080/");
            listener.Start();
            Console.WriteLine("✓ HTTP Server running on http://localhost:8080/");
            Console.WriteLine("✓ Ready for Python commands!");

            // Handle requests
            while (true)
            {
                try
                {
                    var context = await listener.GetContextAsync();
                    _ = Task.Run(() => HandleRequest(context));
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Server error: {ex.Message}");
                }
            }
        }

        private async Task ConnectToIntiface()
        {
            try
            {
                client = new ButtplugClient("Handy Web Server");
                await client.ConnectAsync(new ButtplugWebsocketConnector(new Uri("ws://localhost:12345")));
                Console.WriteLine("✓ Connected to Intiface!");

                // Find device
                await client.StartScanningAsync();
                await Task.Delay(2000);
                await client.StopScanningAsync();

                if (client.Devices.Length > 0)
                {
                    device = client.Devices[0];
                    isConnected = true;
                    Console.WriteLine($"✓ Found device: {device.Name}");
                }
                else
                {
                    Console.WriteLine("❌ No devices found");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Intiface connection failed: {ex.Message}");
            }
        }

        private async Task HandleRequest(HttpListenerContext context)
        {
            var request = context.Request;
            var response = context.Response;

            try
            {
                var path = request.Url.LocalPath;

                if (path.StartsWith("/move/"))
                {
                    // Extract position from URL like /move/0.75
                    if (double.TryParse(path.Substring(6), out double position))
                    {
                        await MoveToPosition(position);
                        await SendResponse(response, "OK");
                    }
                    else
                    {
                        await SendResponse(response, "Invalid position", 400);
                    }
                }
                else if (path == "/pause")
                {
                    await Pause();
                    await SendResponse(response, "Paused");
                }
                else if (path == "/resume")
                {
                    Resume();
                    await SendResponse(response, "Resumed");
                }
                else if (path.StartsWith("/speed/"))
                {
                    // Set speed multiplier like /speed/1.5
                    if (double.TryParse(path.Substring(7), out double speed))
                    {
                        SetSpeed(speed);
                        await SendResponse(response, $"Speed set to {speed}x");
                    }
                    else
                    {
                        await SendResponse(response, "Invalid speed", 400);
                    }
                }
                else if (path == "/status")
                {
                    var status = new
                    {
                        connected = isConnected,
                        paused = isPaused,
                        speed = speedMultiplier,
                        device = device?.Name ?? "None"
                    };
                    await SendResponse(response, JsonSerializer.Serialize(status));
                }
                else
                {
                    await SendResponse(response, "Unknown command", 404);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Request error: {ex.Message}");
                await SendResponse(response, "Internal error", 500);
            }
        }

        private async Task MoveToPosition(double position)
        {
            if (!isConnected || device == null || isPaused)
            {
                return; // Silent fail for smoother operation
            }

            try
            {
                // Clamp position between 0.0 and 1.0
                position = Math.Max(0.0, Math.Min(1.0, position));

                // CLEAN: Let Python handle all smoothing - just send every command
                var baseDuration = 40; // Slightly longer for stability
                var duration = (uint)(baseDuration / speedMultiplier);

                // Ensure minimum duration
                duration = Math.Max(duration, 25);

                await device.LinearAsync(duration, position);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Move error: {ex.Message}");
            }
        }

        private async Task Pause()
        {
            isPaused = true;
            if (isConnected && device != null)
            {
                await device.LinearAsync(1000, 0.0);
                Console.WriteLine("Paused - moved to 0% position");
            }
        }

        private void Resume()
        {
            isPaused = false;
            Console.WriteLine("Resumed");
        }

        private void SetSpeed(double speed)
        {
            speedMultiplier = Math.Max(0.25, Math.Min(2.0, speed));
            Console.WriteLine($"Speed set to {speedMultiplier}x");
        }

        private async Task SendResponse(HttpListenerResponse response, string content, int statusCode = 200)
        {
            response.StatusCode = statusCode;
            response.ContentType = "text/plain";

            var buffer = System.Text.Encoding.UTF8.GetBytes(content);
            response.ContentLength64 = buffer.Length;

            await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
            response.OutputStream.Close();
        }
    }
}