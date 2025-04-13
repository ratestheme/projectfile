import winreg
from PyQt5.QtWidgets import QMessageBox

class RegistryTweaks:
    @staticmethod
    def apply_tweak(window, key_path, value_name, value, value_type, success_msg):
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.SetValueEx(key, value_name, 0, value_type, value)
            winreg.CloseKey(key)
            QMessageBox.information(window, "Success", success_msg)
            return True
        except PermissionError:
            QMessageBox.critical(window, "Error", "Administrator privileges required!")
            return False
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Registry operation failed: {str(e)}")
            return False

    @staticmethod
    def disable_game_bar(window, state):
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR"
        value = 0 if state else 1
        msg = "Game Bar disabled" if state else "Game Bar enabled"
        return RegistryTweaks.apply_tweak(
            window, key_path, "AppCaptureEnabled", value, 
            winreg.REG_DWORD, msg
        )

    @staticmethod
    def disable_fullscreen_optimizations(window, state):
        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        value = 1 if state else 0
        msg = "Fullscreen optimizations disabled" if state else "Fullscreen optimizations enabled"
        return RegistryTweaks.apply_tweak(
            window, key_path, "DisableFullscreenOptimization", value,
            winreg.REG_DWORD, msg
        )

    @staticmethod
    def set_high_performance_power_plan(window, state):
        key_path = r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes"
        value = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" if state else "381b4222-f694-41f0-9685-ff5bb260df2e"
        msg = "High performance power plan enabled" if state else "Balanced power plan enabled"
        return RegistryTweaks.apply_tweak(
            window, key_path, "ActivePowerScheme", value,
            winreg.REG_SZ, msg
        )

    @staticmethod
    def disable_animations(window, state):
        key_path = r"Control Panel\Desktop\WindowMetrics"
        value = "0" if state else "1"
        msg = "Animations disabled" if state else "Animations enabled"
        return RegistryTweaks.apply_tweak(
            window, key_path, "MinAnimate", value,
            winreg.REG_SZ, msg
        )

    @staticmethod
    def optimize_ntfs(window, state):
        key_path = r"SYSTEM\CurrentControlSet\Control\FileSystem"
        value = 1 if state else 0
        msg = "NTFS optimized (last access updates disabled)" if state else "NTFS default settings restored"
        return RegistryTweaks.apply_tweak(
            window, key_path, "NtfsDisableLastAccessUpdate", value,
            winreg.REG_DWORD, msg
        )

    @staticmethod
    def check_registry_state(key_path, value_name, expected_value="1"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return str(value) == expected_value
        except:
            return False