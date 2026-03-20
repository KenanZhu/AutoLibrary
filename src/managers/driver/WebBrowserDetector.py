import platform
import installed_browsers

from pathlib import Path
from enum import Enum
from dataclasses import dataclass


class WebBrowserType(Enum):
    """
        Web browser type
    """

    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


class WebBrowserArch(Enum):
    """
        Web browser architecture
    """

    WINX86_32 = 0
    WINX86_64 = 1
    WINARM = 2

    LINUXX86_32 = 3
    LINUXX86_64 = 4
    LINUXARM = 5

    MACX86_64 = 6
    MACARM = 7

@dataclass
class WebBrowserInfo:
    """
        Web browser information

        Attributes:
            browser_arch (WebBrowserArch): Web browser architecture
            browser_type (WebBrowserType): Web browser type
            browser_version (str): Web browser version
            browser_path (Path): Web browser executable file path
    """

    browser_arch: WebBrowserArch
    browser_type: WebBrowserType
    browser_version: str
    browser_path: Path


class WebBrowserArchDetector:
    """
        Web browser architecture detector
    """

    def __init__(
        self
    ):

        pass


    def detect(
        self
    ) -> WebBrowserArch:
        """
            Detect system architecture

            Returns:
                WebBrowserArch: System architecture
        """

        system = platform.system()
        machine = platform.machine().lower()
        if system == "Windows":
            if machine in ["amd64", "x86_64"]:
                return WebBrowserArch.WINX86_64
            elif machine in ["i386", "i686", "x86"]:
                return WebBrowserArch.WINX86_32
            elif machine in ["arm64", "aarch64"]:
                return WebBrowserArch.WINARM
            else:
                return WebBrowserArch.WINX86_64
        elif system == "Darwin":
            if machine in ["arm64", "aarch64"]:
                return WebBrowserArch.MACARM
            else:
                return WebBrowserArch.MACX86_64
        elif system == "Linux":
            if machine in ["amd64", "x86_64"]:
                return WebBrowserArch.LINUXX86_64
            elif machine in ["i386", "i686", "x86"]:
                return WebBrowserArch.LINUXX86_32
            elif machine in ["arm64", "aarch64"]:
                return WebBrowserArch.LINUXARM
            elif machine.startswith("arm"):
                return WebBrowserArch.LINUXARM
            else:
                return WebBrowserArch.LINUXX86_64
        raise ValueError(f"不支持的系统架构 : {system} {machine}")


class WebBrowserDetector:
    """
        Web browser detector
    """

    def __init__(
        self
    ):

        self.browser_arch = WebBrowserArchDetector().detect()
        self.browser_infos : list[WebBrowserInfo] = []


    def detect(
        self
    ) -> list[WebBrowserInfo]:

        """
            Detect installed web browsers on the system.

            Returns:
                list[WebBrowserInfo]: List of detected browser information objects.
        """

        self.browser_infos = []
        try:
            all_browsers = installed_browsers.browsers()
        except Exception as e:
            self.browser_infos = []
            return self.browser_infos

        # Mapping from internal library name to our enum
        type_map = {
            'chrome': WebBrowserType.CHROME,
            'firefox': WebBrowserType.FIREFOX,
            'msedge': WebBrowserType.EDGE,
        }
        for browser in all_browsers:
            internal_name = browser.get('name', '').lower()
            if internal_name not in type_map:
                continue  # Not one of the browsers we care about
            version = browser.get('version')
            if not version:
                # Skip browsers with no version info (unlikely, but defensive)
                continue
            exe_path = browser.get('location')
            if not exe_path:
                continue
            try:
                path = Path(exe_path)
                if not path.is_file():
                    continue
            except Exception:
                continue  # Invalid path
            info = WebBrowserInfo(
                browser_arch=self.browser_arch,  # Use system architecture as fallback
                browser_type=type_map[internal_name],
                browser_version=version,
                browser_path=path,
            )
            self.browser_infos.append(info)
        return self.browser_infos