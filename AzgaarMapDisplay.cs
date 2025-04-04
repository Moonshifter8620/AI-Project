using UnityEngine;
using System;
using UnityEngine.UI;

public class AzgaarMapDisplay : MonoBehaviour
{
    // Singleton instance
    private static AzgaarMapDisplay _instance;
    public static AzgaarMapDisplay Instance 
    { 
        get 
        {
            if (_instance == null)
            {
                GameObject displayObject = new GameObject("AzgaarMapDisplay");
                _instance = displayObject.AddComponent<AzgaarMapDisplay>();
            }
            return _instance;
        }
    }

    // Map rendering components
    [SerializeField] private RawImage mapRenderTexture;
    [SerializeField] private Camera mapRenderCamera;

    // Map interaction settings
    [SerializeField] private float zoomSpeed = 1f;
    [SerializeField] private float panSpeed = 5f;

    // Current map view state
    private Vector2 currentMapOffset = Vector2.zero;
    private float currentZoomLevel = 1f;

    // Render texture for map display
    private RenderTexture mapTexture;

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

        InitializeMapRenderTexture();
    }

    /// <summary>
    /// Initializes the render texture for map display
    /// </summary>
    private void InitializeMapRenderTexture()
    {
        // Create render texture
        mapTexture = new RenderTexture(Screen.width, Screen.height, 24);
        
        if (mapRenderCamera != null)
        {
            mapRenderCamera.targetTexture = mapTexture;
        }

        if (mapRenderTexture != null)
        {
            mapRenderTexture.texture = mapTexture;
        }
    }

    /// <summary>
    /// Renders the map based on loaded map data
    /// </summary>
    public void RenderMap()
    {
        var mapData = AzgaarIntegrationManager.Instance.CurrentMap;
        
        if (mapData == null)
        {
            Debug.LogWarning("No map data available to render.");
            return;
        }

        // Clear previous rendering
        ClearMapRendering();

        // Render map elements
        RenderLandMasses(mapData);
        RenderRivers(mapData);
        RenderMountains(mapData);
    }

    /// <summary>
    /// Clears the current map rendering
    /// </summary>
    private void ClearMapRendering()
    {
        if (mapRenderCamera != null)
        {
            mapRenderCamera.clearFlags = CameraClearFlags.SolidColor;
            mapRenderCamera.backgroundColor = Color.blue; // Default ocean color
        }
    }

    /// <summary>
    /// Renders land masses
    /// </summary>
    private void RenderLandMasses(AzgaarIntegrationManager.MapData mapData)
    {
        // Placeholder for land mass rendering
        // Will need to be implemented based on specific map data structure
    }

    /// <summary>
    /// Renders rivers
    /// </summary>
    private void RenderRivers(AzgaarIntegrationManager.MapData mapData)
    {
        // Placeholder for river rendering
    }

    /// <summary>
    /// Renders mountains
    /// </summary>
    private void RenderMountains(AzgaarIntegrationManager.MapData mapData)
    {
        // Placeholder for mountain rendering
    }

    /// <summary>
    /// Updates the map view based on user interactions
    /// </summary>
    public void UpdateMapView()
    {
        HandleZooming();
        HandlePanning();
    }

    /// <summary>
    /// Handles map zooming
    /// </summary>
    private void HandleZooming()
    {
        // Get scroll wheel input
        float scrollInput = Input.GetAxis("Mouse ScrollWheel");
        
        // Adjust zoom level
        currentZoomLevel -= scrollInput * zoomSpeed;
        currentZoomLevel = Mathf.Clamp(currentZoomLevel, 0.1f, 10f);

        // Apply zoom to camera
        if (mapRenderCamera != null)
        {
            mapRenderCamera.orthographicSize = currentZoomLevel;
        }
    }

    /// <summary>
    /// Handles map panning
    /// </summary>
    private void HandlePanning()
    {
        // Check for middle mouse button or right mouse button pan
        if (Input.GetMouseButton(2) || Input.GetMouseButton(1))
        {
            Vector2 mouseDelta = new Vector2(
                Input.GetAxis("Mouse X"),
                Input.GetAxis("Mouse Y")
            );

            // Update map offset
            currentMapOffset -= mouseDelta * panSpeed * currentZoomLevel;

            // Apply offset to camera position
            if (mapRenderCamera != null)
            {
                mapRenderCamera.transform.position = new Vector3(
                    currentMapOffset.x,
                    currentMapOffset.y,
                    mapRenderCamera.transform.position.z
                );
            }
        }
    }

    /// <summary>
    /// Scales map to fit Unity view
    /// </summary>
    public void ScaleMapToUnityView()
    {
        // Adjust map scale and positioning
        // Implementation depends on specific map data and requirements
    }

    /// <summary>
    /// Handles various map interactions
    /// </summary>
    public void HandleMapInteractions()
    {
        UpdateMapView();
        
        // Additional interaction logic can be added here
        // Such as:
        // - Clicking on map elements
        // - Selecting regions
        // - Other contextual interactions
    }

    void Update()
    {
        if (AzgaarIntegrationManager.Instance.CurrentMap != null)
        {
            HandleMapInteractions();
        }
    }

    /// <summary>
    /// Cleanup method
    /// </summary>
    void OnDestroy()
    {
        // Clean up render texture
        if (mapTexture != null)
        {
            Destroy(mapTexture);
        }
    }
}
