using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;

public class AzgaarServerUI : MonoBehaviour
{
    // Singleton instance
    private static AzgaarServerUI _instance;
    public static AzgaarServerUI Instance
    {
        get
        {
            if (_instance == null)
            {
                GameObject uiObject = new GameObject("AzgaarServerUI");
                _instance = uiObject.AddComponent<AzgaarServerUI>();
            }
            return _instance;
        }
    }

    // UI Components
    [SerializeField] private Canvas mainCanvas;
    [SerializeField] private Button serverToggleButton;
    [SerializeField] private TextMeshProUGUI serverStatusText;
    [SerializeField] private TextMeshProUGUI mapLoadStatusText;
    [SerializeField] private Button playerModeButton;
    [SerializeField] private Button dmModeButton;

    // Logging
    [SerializeField] private TextMeshProUGUI errorLogText;
    private const int MAX_LOG_ENTRIES = 10;

    // Server connection state
    private bool isServerConnected = false;

    // Flag to prevent automatic map loading through Unity
    [SerializeField] private bool disableUnityMapLoading = true;

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

        InitializeUI();
    }

    /// <summary>
    /// Initializes UI components
    /// </summary>
    private void InitializeUI()
    {
        // Create canvas if not assigned
        if (mainCanvas == null)
        {
            GameObject canvasObject = new GameObject("AzgaarServerUICanvas");
            mainCanvas = canvasObject.AddComponent<Canvas>();
            mainCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvasObject.AddComponent<CanvasScaler>();
            canvasObject.AddComponent<GraphicRaycaster>();
        }

        CreateServerControlUI();
        CreateModeButtons();
    }

    /// <summary>
    /// Creates server control UI elements
    /// </summary>
    public void CreateServerControlUI()
    {
        // Create server toggle button
        if (serverToggleButton == null)
        {
            GameObject buttonObject = new GameObject("ServerToggleButton");
            buttonObject.transform.SetParent(mainCanvas.transform, false);

            serverToggleButton = buttonObject.AddComponent<Button>();
            Image buttonImage = buttonObject.AddComponent<Image>();
            buttonImage.color = Color.gray;

            TextMeshProUGUI buttonText = buttonObject.AddComponent<TextMeshProUGUI>();
            buttonText.text = "Start Server";
            buttonText.color = Color.white;

            // Position button
            RectTransform rectTransform = buttonObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            rectTransform.anchoredPosition = new Vector2(100, -50);
            rectTransform.sizeDelta = new Vector2(150, 50);

            // Add click listener
            serverToggleButton.onClick.AddListener(ToggleServerConnection);
        }

        // Create status text
        if (serverStatusText == null)
        {
            GameObject statusObject = new GameObject("ServerStatusText");
            statusObject.transform.SetParent(mainCanvas.transform, false);

            serverStatusText = statusObject.AddComponent<TextMeshProUGUI>();
            serverStatusText.text = "Server Disconnected";
            serverStatusText.color = Color.red;

            RectTransform rectTransform = statusObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            rectTransform.anchoredPosition = new Vector2(100, -100);
        }
    }

    /// <summary>
    /// Creates mode selection buttons
    /// </summary>
    private void CreateModeButtons()
    {
        // Create Player Mode button
        if (playerModeButton == null)
        {
            GameObject buttonObject = new GameObject("PlayerModeButton");
            buttonObject.transform.SetParent(mainCanvas.transform, false);

            playerModeButton = buttonObject.AddComponent<Button>();
            Image buttonImage = buttonObject.AddComponent<Image>();
            buttonImage.color = Color.green;

            TextMeshProUGUI buttonText = buttonObject.AddComponent<TextMeshProUGUI>();
            buttonText.text = "Launch Player Mode";
            buttonText.color = Color.white;
            buttonText.fontSize = 14;
            buttonText.alignment = TextAlignmentOptions.Center;

            // Position button
            RectTransform rectTransform = buttonObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            rectTransform.anchoredPosition = new Vector2(260, -50);
            rectTransform.sizeDelta = new Vector2(150, 50);

            // Add click listener
            playerModeButton.onClick.AddListener(() => LaunchPlayerMode());
        }

        // Create DM Mode button
        if (dmModeButton == null)
        {
            GameObject buttonObject = new GameObject("DMModeButton");
            buttonObject.transform.SetParent(mainCanvas.transform, false);

            dmModeButton = buttonObject.AddComponent<Button>();
            Image buttonImage = buttonObject.AddComponent<Image>();
            buttonImage.color = new Color(0.7f, 0.0f, 0.0f); // Dark red

            TextMeshProUGUI buttonText = buttonObject.AddComponent<TextMeshProUGUI>();
            buttonText.text = "Launch DM Mode";
            buttonText.color = Color.white;
            buttonText.fontSize = 14;
            buttonText.alignment = TextAlignmentOptions.Center;

            // Position button
            RectTransform rectTransform = buttonObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            rectTransform.anchoredPosition = new Vector2(420, -50);
            rectTransform.sizeDelta = new Vector2(150, 50);

            // Add click listener
            dmModeButton.onClick.AddListener(() => LaunchDMMode());
        }
    }

    /// <summary>
    /// Toggles server connection
    /// </summary>
    public void ToggleServerConnection()
    {
        if (!isServerConnected)
        {
            StartServer();
        }
        else
        {
            StopServer();
        }
    }

    /// <summary>
    /// Starts the local server
    /// </summary>
    private void StartServer()
    {
        try
        {
            AzgaarLocalServer.Instance.StartServer();

            // Update UI
            isServerConnected = true;
            serverToggleButton.GetComponentInChildren<TextMeshProUGUI>().text = "Stop Server";
            serverStatusText.text = "Server Running";
            serverStatusText.color = Color.green;

            // Attempt to initialize map only if not disabled
            if (!disableUnityMapLoading)
            {
                AzgaarIntegrationManager.Instance.InitializeMap();
            }
            else
            {
                // Update map load status without actually loading the map
                // UpdateMapLoadStatus("Map loading handled in browser", false);
            }
        }
        catch (Exception ex)
        {
            LogError($"Server start failed: {ex.Message}");
        }
    }

    /// <summary>
    /// Stops the local server
    /// </summary>
    private void StopServer()
    {
        try
        {
            AzgaarLocalServer.Instance.StopServer();

            // Update UI
            isServerConnected = false;
            serverToggleButton.GetComponentInChildren<TextMeshProUGUI>().text = "Start Server";
            serverStatusText.text = "Server Disconnected";
            serverStatusText.color = Color.red;
        }
        catch (Exception ex)
        {
            LogError($"Server stop failed: {ex.Message}");
        }
    }

    /// <summary>
    /// Launches the Player Mode - new combined function that starts server if needed
    /// </summary>
    public void LaunchPlayerMode()
    {
        try
        {
            // Start server if not already running
            if (!isServerConnected)
            {
                StartServer();
            }

            string url = $"http://localhost:{AzgaarLocalServer.Instance.ServerPort}/index.html?playermode=1";
            Debug.Log($"Opening browser in Player Mode: {url}");
            Application.OpenURL(url);
        }
        catch (Exception ex)
        {
            LogError($"Launch Player Mode failed: {ex.Message}");
        }
    }

    /// <summary>
    /// Launches the DM Mode - new combined function that starts server if needed
    /// </summary>
    public void LaunchDMMode()
    {
        try
        {
            // Start server if not already running
            if (!isServerConnected)
            {
                StartServer();
            }

            string url = $"http://localhost:{AzgaarLocalServer.Instance.ServerPort}/index.html";
            Debug.Log($"Opening browser in DM Mode: {url}");
            Application.OpenURL(url);
        }
        catch (Exception ex)
        {
            LogError($"Launch DM Mode failed: {ex.Message}");
        }
    }

    /// <summary>
    /// Updates map load status
    /// </summary>
    public void UpdateMapLoadStatus(string status, bool isError = false)
    {
        if (mapLoadStatusText == null)
        {
            GameObject statusObject = new GameObject("MapLoadStatusText");
            statusObject.transform.SetParent(mainCanvas.transform, false);

            mapLoadStatusText = statusObject.AddComponent<TextMeshProUGUI>();

            RectTransform rectTransform = statusObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            rectTransform.anchoredPosition = new Vector2(100, -150);
        }

        mapLoadStatusText.text = status;
        mapLoadStatusText.color = isError ? Color.red : Color.black;
    }

    /// <summary>
    /// Logs errors to UI
    /// </summary>
    public void LogError(string errorMessage)
    {
        Debug.LogError(errorMessage);

        if (errorLogText == null)
        {
            GameObject logObject = new GameObject("ErrorLogText");
            logObject.transform.SetParent(mainCanvas.transform, false);

            errorLogText = logObject.AddComponent<TextMeshProUGUI>();

            RectTransform rectTransform = logObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 0);
            rectTransform.anchorMax = new Vector2(0, 0);
            rectTransform.anchoredPosition = new Vector2(100, 50);
            rectTransform.sizeDelta = new Vector2(300, 200);
        }

        // Append new error, limit to MAX_LOG_ENTRIES
        string[] currentErrors = errorLogText.text.Split('\n');
        string newErrorLog = errorMessage + "\n";

        for (int i = 0; i < Mathf.Min(currentErrors.Length, MAX_LOG_ENTRIES - 1); i++)
        {
            newErrorLog += currentErrors[i] + "\n";
        }

        errorLogText.text = newErrorLog;
    }
}