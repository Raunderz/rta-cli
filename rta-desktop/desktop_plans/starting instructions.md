Here's your quick reference. Save this as `RUN.md` in your project root:

---

# How to Run RTA Desktop

## Every Time You Start Working

```bash
cd /home/poser/Documents/github_work/Rta/rta-desktop
nix develop
```

## If You Haven't Built Yet (or Cleaned)
```bash
yarn build:browser
```

## Start the App
```bash
yarn start:browser
```
Then open: **http://localhost:3000**

---

## Quick Cheat Sheet

| Situation | Command |
|-----------|---------|
| First time today | `nix develop` |
| Changed extension code | `yarn build:browser` then `yarn start:browser` |
| Added new dependencies | Ctrl+C, `yarn`, then `yarn build:browser && yarn start:browser` |
| Watch mode (auto-rebuild) | `yarn watch:browser` (in one terminal) + `yarn start:browser` (in another) |
| Build desktop app | `yarn build:electron` then `yarn start:electron` |
| Stop the app | `Ctrl+C` |
| Exit Nix shell | `exit` |

---

## Your Extension Code Lives Here
```
./rta-desktop/
```
Changes go there. The browser app includes it automatically.