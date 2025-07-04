using Buttplug;
using Buttplug.Client;
using System;
using System.IO;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;
using System.Threading;

namespace handyman
{
    class HandyServer
    {
        private ButtplugClient client;
        private DateTime _lastMoveTime = DateTime.UtcNow;  // Track last send time for smooth ramping
        private ButtplugClientDevice device;
        private bool isConnected = false;
        private bool isPaused = true;
        private double speedMultiplier = 1.0;
        private double lastPosition = 0.0;
        private readonly object moveLock = new object();

        static async Task Main(string[] args)
        {
            var server = new HandyServer();
            await server.Start();
        }

        public async Task Start()
        {
            Console.WriteLine("Starting Improved Handy Web Server...");

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
                await Task.Delay(3000);
                await client.StopScanningAsync();

                if (client.Devices.Length > 0)
                {
                    device = client.Devices[0];
                    isConnected = true;
                    Console.WriteLine($"✓ Found device: {device.Name}");

                    // Test initial movement
                    await TestDeviceMovement();
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

        private async Task TestDeviceMovement()
        {
            try
            {
                Console.WriteLine("Testing device movement...");
                await device.LinearAsync(500, 0.5);
                await Task.Delay(500);
                await device.LinearAsync(500, 0.0);
                Console.WriteLine("✓ Device movement test successful");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Device movement test failed: {ex.Message}");
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
                    device = device?.Name ?? "None",
                    lastPosition = lastPosition,
                    lastMoveTime = _lastMoveTime.ToString("HH:mm:ss.fff")
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
                return;
            }

            try
            {
                // Clamp position between 0.0 and 1.0
                position = Math.Max(0.0, Math.Min(1.0, position));

                // Calculate ms since last update (clamped 15–100 ms)
                var now = DateTime.UtcNow;
                var msSince = (uint)(now - _lastMoveTime).TotalMilliseconds;
                _lastMoveTime = now;
                var duration = Math.Max(15u, Math.Min(100u, msSince));

                // Ramp over that measured interval
                await device.LinearAsync(duration, position);

                // Track last position
                lastPosition = position;
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
                try
                {
                    await device.LinearAsync(1000, 0.0);
                    lastPosition = 0.0;
                    _lastMoveTime = DateTime.UtcNow;
                    Console.WriteLine("✓ Paused - moved to 0% position");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Pause error: {ex.Message}");
                }
            }
        }

        private void Resume()
        {
            isPaused = false;
            Console.WriteLine("✓ Resumed");
        }

        private void SetSpeed(double speed)
        {
            speedMultiplier = Math.Max(0.25, Math.Min(3.0, speed));
            Console.WriteLine($"✓ Speed set to {speedMultiplier:F1}x");
        }

        private async Task SendResponse(HttpListenerResponse response, string content, int statusCode = 200)
        {
            try
            {
                response.StatusCode = statusCode;
                response.ContentType = "application/json";
                response.Headers.Add("Access-Control-Allow-Origin", "*");

                var buffer = System.Text.Encoding.UTF8.GetBytes(content);
                response.ContentLength64 = buffer.Length;

                await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                response.OutputStream.Close();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Response error: {ex.Message}");
            }
        }
    }
}
