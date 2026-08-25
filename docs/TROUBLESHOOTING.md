# Troubleshooting & Diagnostics

## Common Issues & Solutions

### 1. "No Stegstr payload detected"
- **Cause**: Image was severely cropped or downscaled beyond 50%.
- **Solution**: Re-encode carrier with `--robustness robust` or `--robustness maximum` mode.

### 2. "Relay connection offline"
- **Cause**: Network disconnection or relay server downtime.
- **Solution**: Run `./stegstr-cli relay test` to test active relays. Messages created offline will automatically queue in SQLite and sync upon network recovery.
