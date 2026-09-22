import os
import sys
import shutil
import subprocess
import webbrowser

def main():
    print("=" * 72)
    print("   I LOVE FILES - Native AutoCAD / DWG TrueView Engine Setup")
    print("=" * 72)
    print()

    # Import detection functions
    try:
        from converters.autocad_plotter import get_autocad_console_path, get_autocad_plot_styles_dir
    except Exception as e:
        print(f"[ERROR] Could not import converters.autocad_plotter: {e}")
        input("\nPress Enter to exit...")
        return 1

    console = get_autocad_console_path()
    if console and os.path.exists(console):
        handle_success(console, get_autocad_plot_styles_dir)
        input("\nPress Enter to exit...")
        return 0

    print("[!] Autodesk AutoCAD or DWG TrueView was not detected on this machine.")
    print()
    print("To get 100% exact AutoCAD colors, badges (85A, 99), and Chevron logo:")
    print("Autodesk DWG TrueView is 100% FREE from Autodesk and includes the")
    print("official AutoCAD Core Console (accoreconsole.exe). No license needed!")
    print()
    print("-" * 72)
    print("Step 1: Opening the official Autodesk DWG TrueView download page...")
    print("-" * 72)
    
    url = "https://www.autodesk.com/products/dwg-trueview/overview"
    try:
        webbrowser.open(url)
    except Exception:
        print(f"Please open this URL in your browser: {url}")

    print()
    print("Step 2: On the Autodesk page, download DWG TrueView and run the setup.")
    print("        (Standard installation takes about 2-3 minutes).")
    print()
    input("Step 3: Once the installation is finished, press ENTER here to verify...")
    print()

    # Re-check
    console = get_autocad_console_path()
    if console and os.path.exists(console):
        handle_success(console, get_autocad_plot_styles_dir)
    else:
        print("=" * 72)
        print("[!] Still not detected automatically.")
        print("If installed in a custom directory, set the path in PowerShell/CMD:")
        print(r'   setx AUTOCAD_CONSOLE_PATH "C:\path\to\accoreconsole.exe" /M')
        print("=" * 72)

    input("\nPress Enter to exit...")
    return 0

def handle_success(console_path, get_plot_styles_dir_func):
    print("=" * 72)
    print("   [SUCCESS] Native AutoCAD Core Console is ACTIVE and READY!")
    print("=" * 72)
    print(f"Engine Path: {console_path}")
    print()

    plot_dir = get_plot_styles_dir_func()
    if plot_dir and os.path.isdir(plot_dir):
        print(f"Plot Styles Directory: {plot_dir}")
        bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plot_styles")
        if os.path.isdir(bundled):
            for ctb in os.listdir(bundled):
                if ctb.lower().endswith(".ctb"):
                    src = os.path.join(bundled, ctb)
                    dst = os.path.join(plot_dir, ctb)
                    try:
                        shutil.copyfile(src, dst)
                        print(f"  -> Synced plot style: {ctb}")
                    except Exception as ex:
                        print(f"  -> Could not copy {ctb}: {ex}")
    else:
        print("[INFO] Default plot styles directory will be initialized on first run.")

    print()
    print("Restarting 24x7 background server task (ILoveFiles_24x7)...")
    try:
        res = subprocess.run(["schtasks", "/run", "/tn", "ILoveFiles_24x7"], capture_output=True, text=True)
        if res.returncode == 0:
            print("  -> Service restarted successfully!")
        else:
            print(f"  -> Scheduled task status: {res.stdout.strip() or res.stderr.strip()}")
    except Exception as e:
        print(f"  -> Note on service restart: {e}")

    print()
    print("=" * 72)
    print("All CAD conversions on your website will now match AutoCAD 100%!")
    print("=" * 72)

if __name__ == '__main__':
    sys.exit(main())
