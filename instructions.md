# Getting Started with Expo & React Native (using Bun)

This project has been set up using [Expo](https://expo.dev/) and [Bun](https://bun.sh/) as the package manager.

## Project Structure

- `app/`: The React Native + Expo project directory.
- `LICENSE`: The project's license.
- `README.md`: Original project overview.
- `instructions.md`: This file.

## How to Run the App

Navigate to the `app/` directory and use Bun to start the development server:

```bash
cd app
bun run start
```

### Platform-Specific Commands

- **Android:** `bun run android`
- **iOS:** `bun run ios` (requires macOS)
- **Web:** `bun run web`

## Moving Forward

### 1. Adding New Dependencies
To add new packages, use `bun add`:

```bash
cd app
bun add <package-name>
# For dev dependencies:
bun add -d <package-name>
```

### 2. Project Organization
Consider organizing your code in `app/src/`:
- `app/src/components/`: Reusable UI components.
- `app/src/screens/`: Main application screens.
- `app/src/navigation/`: Navigation logic (e.g., React Navigation or Expo Router).
- `app/src/hooks/`: Custom React hooks.
- `app/src/utils/`: Utility functions and constants.

### 3. Recommended Tools
- **Expo Go:** Install the "Expo Go" app on your physical device to test the app without a full native build.
- **VS Code Extensions:**
  - `Expo Tools`
  - `ESLint`
  - `Prettier`

### 4. Next Steps
- Update `app/App.js` to start building your UI.
- Explore the [Expo Documentation](https://docs.expo.dev/) for more advanced features like push notifications, camera, and maps.
- If you need navigation, consider setting up [Expo Router](https://docs.expo.dev/router/introduction/).
