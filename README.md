# LKS QuadGrab
<img width="1665" height="864" alt="image" src="https://github.com/user-attachments/assets/f97fc6c0-a880-4d2c-8889-60d20247cb67" />

LKS QuadGrab is a Blender add-on that allows you to use a quad (mesh object) as a reference plane to capture textures from the scene. It simplifies the process of baking textures from complex geometry onto a simple plane, and includes boilerplate for setting up a preview material and modifier stack with the baked textures.
This was written for Blender 5.1 after a bunch of api updates, I probably wouldn't try to use it in a version of blender before 5.0

Here's a demo of what it's for and how to use it
https://youtu.be/Y562RmPBJwI

## Installation

### Manual Installation
1. Download the add-on as a `.zip` file.
2. In Blender, go to **Edit > Preferences > Get Extensions**.
3. Click the **Install from Disk...** button (or drag and drop the `.zip` file).
4. Select the downloaded `.zip` file and click **Install from Disk**.
5. Enable the add-on by checking the box next to **LKS QuadGrab**.

### Automatic Updates (Blender 5.0+)
To receive automatic updates directly within Blender, you can add our custom Extension Repository:
1. In Blender, go to **Edit > Preferences > Get Extensions**.
2. Click the dropdown menu (chevron) in the top right corner and select **Repositories**.
3. Click the **+** button to add a new repository.
4. Set the **URL** to: `https://liamsmyth.github.io/LKS_QuadGrab/index.json`
5. Give it a name (e.g., "LKS Extensions") and click **Create**.
6. You can now install and update LKS QuadGrab directly from the **Get Extensions** tab.

## Testing

### Headless Test Suite (addon)
Runs the unit/integration tests against the local addon tree:
```
launch_headless_test.bat
```

### Sandbox Extension Test
Because the local workspace contains dev files that are excluded from the published extension, it's important to verify the **packaged** extension loads correctly. The sandbox test builds (or pulls) the extension zip, extracts it to an isolated temp directory, and runs Blender headless against it.

**Test the local build** (verifies `blender_manifest.toml` paths are correct):
```
test_sandbox_extension.bat
```

**Test the published remote** (verifies what users actually download from gh-pages):
```
test_sandbox_extension.bat --remote
```

> **Important:** Always run `test_sandbox_extension.bat --remote` after publishing a release to confirm the deployed extension installs and registers cleanly. A feature should not be considered complete until the sandbox test passes.
