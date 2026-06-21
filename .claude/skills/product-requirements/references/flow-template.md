# Screen Flows & Navigation Template (ADA911 Format)

## Activity Map Format

Table listing all screens with package paths.

```
### 4.1 Activity Map

| # | Screen | Package Path | Description |
|---|--------|-------------|-------------|
| 1 | `SplashScreen` | `presentation.splash` | App launcher |
| 2 | `HomeScreen` | `presentation.home` | Main screen with tabs |
| 3 | `SettingsScreen` | `presentation.settings` | App settings |
```

## Navigation Structure Format

ASCII tree diagram showing app navigation hierarchy.

```
### 4.2 App Navigation Structure

App Launch
    |
    +--> [Splash]
           |
           +--> First Launch: [Onboarding] --> [Home]
           |
           +--> Returning User: --> [Home]
                                       |
           +---------------------------+
           |                           |
      [Tab 1]                     [Tab 2]
           |                           |
      [Feature A]                [Feature B]
```

## Key User Flows Format

Step-by-step flow with decision points.

```
### 4.3 Key User Flows

#### Flow 1: [Flow Name] ([User Type])

Home Screen
  --> Tap "[Feature]"
  --> [Config Screen]
  --> Configure parameters
  --> Tap "[Action]"
  --> [Processing Screen] (progress 0% -> 100%)
  --> [Result Screen]
  --> Save / Share
  --> [END]
```

## Guidelines

- Activity Map: list ALL screens with unique package paths
- Navigation Structure: show full hierarchy with ASCII tree
- User Flows: cover primary happy paths + key branching (free vs premium)
- Include decision points for conditional navigation
- Document error/retry flows separately
