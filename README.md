# LKS QuadGrab

LKS QuadGrab is a Blender add-on that allows you to use a quad (mesh object) as a reference plane to capture textures from the scene. It simplifies the process of baking textures from complex geometry onto a simple plane, and includes boilerplate for setting up a preview material and modifier stack with the baked textures.

## Features

- **Texture Capture:** Use any quad mesh as a reference plane to capture textures (Base Color, Normal, Roughness, Metallic, Specular, AO, Alpha, Z-Depth) from the surrounding scene.
- **Preview Setup:** Automatically generates a preview plane with a material and displacement modifier stack using the captured textures.
- **Customizable Output:** Configure output resolution, depth limits, and which texture maps to generate.

## Installation

### Manual Installation
1. Download the add-on as a `.zip` file.
2. In Blender, go to **Edit > Preferences > Get Extensions**.
3. Click the **Install from Disk...** button (or drag and drop the `.zip` file).
4. Select the downloaded `.zip` file and click **Install from Disk**.
5. Enable the add-on by checking the box next to **LKS QuadGrab**.

### Automatic Updates (Blender 4.2+)
To receive automatic updates directly within Blender, you can add our custom Extension Repository:
1. In Blender, go to **Edit > Preferences > Get Extensions**.
2. Click the dropdown menu (chevron) in the top right corner and select **Repositories**.
3. Click the **+** button to add a new repository.
4. Set the **URL** to: `https://liamsmyth.github.io/LKS_QuadGrab/`
5. Give it a name (e.g., "LKS Extensions") and click **Create**.
6. You can now install and update LKS QuadGrab directly from the **Get Extensions** tab.

## Usage

1. Open the **3D Viewport** and press `N` to open the sidebar.
2. Navigate to the **LKS** tab and find the **LKS QuadGrab** panel.
3. Configure your desired output settings (resolution, output directory, maps to generate).
4. Click **Make QuadGrab Plane** to create a reference plane in your scene.
5. Position and scale the plane to cover the area you want to capture.
6. Click **QuadGrab** to capture the textures.
7. (Optional) If **Create Preview Plane** is enabled, a new plane will be created with the captured textures applied.
8. Click **Cleanup QuadGrab Objects** to remove the reference plane and any intermediate objects.
