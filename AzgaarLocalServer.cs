using UnityEngine;
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using System.IO;
using System.Text;

public class AzgaarLocalServer : MonoBehaviour
{
    // Server configuration
    [SerializeField] private int serverPort = 8080;
    private HttpListener listener;
    private CancellationTokenSource cancellationTokenSource;
    private bool isServerRunning = false;

    // Azgaar Viewer directory path
    [SerializeField] private string azgaarViewerPath = "AzgaarViewer/Fantasy-Map-Generator-master";

    // Absolute path for development
    private readonly string customAbsolutePath = @"C:\Users\brian\Mapping Project\Assets\AzgaarViewer\Fantasy-Map-Generator-master";

    // Toggle to use absolute path instead of relative
    [SerializeField] private bool useAbsolutePath = true;

    // Path to the test map file
    [SerializeField] private string testMapPath = "Maps/test.map";

    // Flag to disable Unity's map loading
    [SerializeField] private bool disableUnityMapLoading = true;

    // Property to expose the server port
    public int ServerPort => serverPort;

    // Singleton pattern to ensure only one instance
    private static AzgaarLocalServer _instance;
    public static AzgaarLocalServer Instance
    {
        get
        {
            if (_instance == null)
            {
                GameObject serverObject = new GameObject("AzgaarLocalServer");
                _instance = serverObject.AddComponent<AzgaarLocalServer>();
            }
            return _instance;
        }
    }

    void Awake()
    {
        // Ensure singleton
        if (_instance != null && _instance != this)
        {
            Destroy(this.gameObject);
            return;
        }
        _instance = this;
        DontDestroyOnLoad(this.gameObject);
    }

    /// <summary>
    /// Opens browser to local server with parameters to load test map
    /// </summary>
    private void OpenBrowserToLocalhost()
    {
        string url = $"http://localhost:{serverPort}/index.html?loadmap=1";
        Debug.Log($"Opening browser to URL: {url}");
        Application.OpenURL(url);
    }

    /// <summary>
    /// Creates a custom index.html with auto-load script and mode modifications
    /// </summary>
    private string GetModifiedIndexHtml(string originalContent, bool isPlayerMode = false)
    {
        string scriptToInject;

        if (isPlayerMode)
        {
            // Player Mode
            scriptToInject = @"
<style>
    /* Hide unwanted tabs */
    #styleButton, #optionsButton, #toolsButton, #aboutButton {
        display: none !important;
    }
    
    /* Hide tab content */
    #styleContent, #optionsContent, #toolsContent, #aboutContent {
        display: none !important;
    }
    
    /* Hide loading screens */
    #loading, .loading, .notification, #notificationContainer {
        display: none !important;
    }
</style>
<script>
    window.addEventListener('load', function() {
        console.log('Adding Player Mode indicator');
        
        // Hide loading elements
        document.querySelectorAll('#loading, .loading, .notification, #notificationContainer').forEach(function(el) {
            if (el) el.style.display = 'none';
        });
        
        // Create Player Mode indicator
        var modeBanner = document.createElement('div');
        modeBanner.style.position = 'fixed';
        modeBanner.style.top = '5px';
        modeBanner.style.right = '50px';
        modeBanner.style.padding = '5px 10px';
        modeBanner.style.backgroundColor = 'rgba(0, 100, 0, 0.7)';
        modeBanner.style.color = 'white';
        modeBanner.style.borderRadius = '5px';
        modeBanner.style.fontSize = '14px';
        modeBanner.style.zIndex = '9999';
        modeBanner.textContent = 'Player Mode';
        document.body.appendChild(modeBanner);
        
        console.log('Player Mode setup complete');
    });
</script>";
        }
        else
        {
            // DM Mode
            scriptToInject = @"
<style>
    /* Hide loading screens */
    #loading, .loading, .notification, #notificationContainer {
        display: none !important;
    }
</style>
<script>
    window.addEventListener('load', function() {
        console.log('Adding DM Mode indicator');
        
        // Hide loading elements
        document.querySelectorAll('#loading, .loading, .notification, #notificationContainer').forEach(function(el) {
            if (el) el.style.display = 'none';
        });
        
        // Create DM Mode indicator
        var modeBanner = document.createElement('div');
        modeBanner.style.position = 'fixed';
        modeBanner.style.top = '5px';
        modeBanner.style.right = '50px';
        modeBanner.style.padding = '5px 10px';
        modeBanner.style.backgroundColor = 'rgba(139, 0, 0, 0.7)';
        modeBanner.style.color = 'white';
        modeBanner.style.borderRadius = '5px';
        modeBanner.style.fontSize = '14px';
        modeBanner.style.zIndex = '9999';
        modeBanner.textContent = 'DM Mode';
        document.body.appendChild(modeBanner);
        
        console.log('DM Mode setup complete');
    });
</script>";
        }

        // Add a more targeted style for the loading screen only
        int headIndex = originalContent.IndexOf("</head>");
        if (headIndex != -1)
        {
            string immediateStyle = @"
<style>
    /* Make just the loading screen elements transparent */
    #loading, #loading-rose, #loading svg, #initial {
        opacity: 0 !important;
    }
    /* Hide the specific fill elements within the loading screen */
    #loading rect {
        fill: transparent !important;
    }
</style>";
            originalContent = originalContent.Insert(headIndex, immediateStyle);
        }

        // Insert the script at the end of the body for guaranteed DOM access
        int bodyEndIndex = originalContent.LastIndexOf("</body>");
        if (bodyEndIndex != -1)
        {
            return originalContent.Insert(bodyEndIndex, scriptToInject);
        }
        else
        {
            // If no body end tag found, try head
            int headEndIndex = originalContent.IndexOf("</head>");
            if (headEndIndex != -1)
            {
                return originalContent.Insert(headEndIndex, scriptToInject);
            }
            else
            {
                // Last resort
                return originalContent + scriptToInject;
            }
        }
    }

    /// <summary>
    /// Starts the local HTTP server
    /// </summary>
    public void StartServer()
    {
        // If server is already running, stop it first
        if (isServerRunning)
        {
            StopServer();
        }

        try
        {
            // Get full path to viewer directory
            string fullViewerPath;

            if (useAbsolutePath)
            {
                // Use the hardcoded absolute path
                fullViewerPath = customAbsolutePath;
            }
            else
            {
                // Use the relative path combined with Application.dataPath
                fullViewerPath = Path.Combine(Application.dataPath, azgaarViewerPath);
            }

            // Normalize path separators for consistency
            fullViewerPath = fullViewerPath.Replace('\\', '/');
            Debug.Log($"Looking for viewer directory at: {fullViewerPath}");

            if (!Directory.Exists(fullViewerPath))
            {
                Debug.LogError($"Azgaar viewer directory not found at: {fullViewerPath}");
                Debug.Log("Please create this directory and place the Azgaar Fantasy Map Generator files there.");
                return;
            }

            // Create a new HttpListener and cancellation token
            listener = new HttpListener();
            listener.Prefixes.Add($"http://localhost:{serverPort}/");
            listener.Start();
            isServerRunning = true;

            Debug.Log($"Server started on port {serverPort}");

            // Prevent Unity from loading a map if the flag is set
            if (disableUnityMapLoading)
            {
                // We'll handle notifying the integration manager separately
                // Do not call AzgaarIntegrationManager.Instance.InitializeMap();
            }

            OpenBrowserToLocalhost();

            // Create a new cancellation token source
            cancellationTokenSource = new CancellationTokenSource();

            // Start listening in a separate task
            Task.Run(() => ListenForRequests(cancellationTokenSource.Token));
        }
        catch (Exception ex)
        {
            Debug.LogError($"Server start error: {ex.Message}");
            StopServer();
        }
    }

    /// <summary>
    /// Listens for incoming HTTP requests
    /// </summary>
    private async Task ListenForRequests(CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                HttpListenerContext context;
                try
                {
                    context = await Task.Run(() => listener.GetContext(), cancellationToken);
                    ProcessRequest(context);
                }
                catch (OperationCanceledException)
                {
                    // Normal cancellation, break the loop
                    break;
                }
                catch (HttpListenerException ex)
                {
                    // Handle specific HTTP listener exceptions
                    Debug.Log($"HTTP Listener error: {ex.Message}");
                    break;
                }
                catch (Exception ex)
                {
                    // Log other unexpected errors
                    Debug.LogError($"Request listening error: {ex.Message}");
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            // Catch any outer exceptions during the listening process
            Debug.LogError($"Unexpected server listening error: {ex.Message}");
        }
        finally
        {
            // Ensure cleanup occurs
            Debug.Log("Server listening task completed.");
        }
    }

    /// <summary>
    /// Processes incoming HTTP requests
    /// </summary>
    private void ProcessRequest(HttpListenerContext context)
    {
        try
        {
            string requestPath = context.Request.Url.LocalPath;

            // Log the requested path
            Debug.Log($"Request received for: {requestPath}");

            // If root path, serve index.html
            if (requestPath == "/" || requestPath == "")
            {
                ServeFile(context, "index.html");
                return;
            }

            // Special handling for map file requests
            if (requestPath.EndsWith(".map") || requestPath.EndsWith("test.map"))
            {
                ServeMapFile(context, Path.GetFileName(requestPath));
                return;
            }

            // Serve requested file
            ServeFile(context, requestPath.TrimStart('/'));
        }
        catch (Exception ex)
        {
            Debug.LogError($"Request processing error: {ex.Message}");
            context.Response.StatusCode = 500;
            context.Response.Close();
        }
    }

    /// <summary>
    /// Serves the test map file
    /// </summary>
    private void ServeMapFile(HttpListenerContext context, string fileName)
    {
        try
        {
            string mapFullPath;

            if (useAbsolutePath)
            {
                // Use absolute path but go up one level to get to the Maps folder
                mapFullPath = Path.Combine(customAbsolutePath, "..", testMapPath);
            }
            else
            {
                // Use the relative path to the map file
                mapFullPath = Path.Combine(Application.dataPath, testMapPath);
            }

            // Normalize path separators
            mapFullPath = mapFullPath.Replace('\\', '/');

            Debug.Log($"Serving map file from: {mapFullPath}");

            if (!File.Exists(mapFullPath))
            {
                Debug.LogError($"Map file not found at: {mapFullPath}");
                context.Response.StatusCode = 404;
                context.Response.Close();
                return;
            }

            byte[] fileBytes = File.ReadAllBytes(mapFullPath);
            context.Response.ContentType = "application/octet-stream";
            context.Response.ContentLength64 = fileBytes.Length;

            using (var output = context.Response.OutputStream)
            {
                output.Write(fileBytes, 0, fileBytes.Length);
            }

            context.Response.Close();
        }
        catch (Exception ex)
        {
            Debug.LogError($"Map file serving error: {ex.Message}");
            context.Response.StatusCode = 500;
            context.Response.Close();
        }
    }

    /// <summary>
    /// Serves a file from the Azgaar Viewer directory
    /// </summary>
    private void ServeFile(HttpListenerContext context, string requestedFile)
    {
        try
        {
            string fullPath;
            bool isPlayerMode = context.Request.Url.Query != null && context.Request.Url.Query.Contains("playermode=1");
            Debug.Log($"Request mode: {(isPlayerMode ? "Player Mode" : "DM Mode")}");

            if (useAbsolutePath)
            {
                // Use the hardcoded absolute path (always use the main index.html)
                fullPath = Path.Combine(customAbsolutePath, requestedFile);
            }
            else
            {
                // Use the relative path combined with Application.dataPath
                fullPath = Path.Combine(Application.dataPath, azgaarViewerPath, requestedFile);
            }

            // Normalize path separators for consistency
            fullPath = fullPath.Replace('\\', '/');
            Debug.Log($"Trying to serve file: {fullPath}");

            if (!File.Exists(fullPath))
            {
                Debug.LogError($"File not found at: {fullPath}");
                context.Response.StatusCode = 404;
                context.Response.Close();
                return;
            }

            // Determine content type based on file extension
            string contentType = GetContentType(Path.GetExtension(fullPath));

            // For index.html, we want to modify it based on the mode
            if (requestedFile.EndsWith("index.html"))
            {
                string originalContent = File.ReadAllText(fullPath);
                string modifiedContent = GetModifiedIndexHtml(originalContent, isPlayerMode);

                byte[] contentBytes = Encoding.UTF8.GetBytes(modifiedContent);
                context.Response.ContentType = contentType;
                context.Response.ContentLength64 = contentBytes.Length;

                using (var output = context.Response.OutputStream)
                {
                    output.Write(contentBytes, 0, contentBytes.Length);
                }
            }
            else
            {
                // For all other files, serve as-is
                byte[] fileBytes = File.ReadAllBytes(fullPath);
                context.Response.ContentType = contentType;
                context.Response.ContentLength64 = fileBytes.Length;

                using (var output = context.Response.OutputStream)
                {
                    output.Write(fileBytes, 0, fileBytes.Length);
                }
            }

            context.Response.Close();
        }
        catch (Exception ex)
        {
            Debug.LogError($"File serving error: {ex.Message}");
            context.Response.StatusCode = 500;
            context.Response.Close();
        }
    }

    /// <summary>
    /// Determines the MIME content type based on file extension
    /// </summary>
    private string GetContentType(string fileExtension)
    {
        switch (fileExtension.ToLower())
        {
            case ".html":
                return "text/html";
            case ".css":
                return "text/css";
            case ".js":
                return "application/javascript";
            case ".json":
                return "application/json";
            case ".png":
                return "image/png";
            case ".jpg":
            case ".jpeg":
                return "image/jpeg";
            case ".svg":
                return "image/svg+xml";
            case ".txt":
                return "text/plain";
            case ".map":
                return "application/octet-stream";
            default:
                return "application/octet-stream";
        }
    }

    /// <summary>
    /// Stops the local server
    /// </summary>
    public void StopServer()
    {
        Debug.Log("Attempting to stop server");

        try
        {
            // Cancel any ongoing operations
            if (cancellationTokenSource != null)
            {
                cancellationTokenSource.Cancel();
                cancellationTokenSource.Dispose();
                cancellationTokenSource = null;
            }

            // Stop and close the listener
            if (listener != null)
            {
                listener.Stop();
                listener.Close();
                listener = null;
            }

            isServerRunning = false;
            Debug.Log("Server stopped.");
        }
        catch (Exception ex)
        {
            Debug.LogError($"Server stop error: {ex.Message}");
        }
    }

    // Cleanup on application quit
    void OnApplicationQuit()
    {
        StopServer();
    }
}