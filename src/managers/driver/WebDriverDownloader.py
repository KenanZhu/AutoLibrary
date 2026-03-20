import os
import time
import shutil
import requests
import zipfile
import tarfile

from enum import Enum
from pathlib import Path
from typing import Optional, Callable


class WebDriverType(Enum):
    """
        Web driver type
    """

    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


class WebDriverArch(Enum):
    """
        Web driver architecture
    """

    class Chrome(Enum):
        """
            Chrome web driver architecture
        """

        WINX86_32 = "win32"
        WINX86_64 = "win64"

        # LINUX86_32 : no support for linux 32bit
        LINUX86_64 = "linux64"
        # LINUXARM : no support for linux arm64

        MACX86_64 = "mac-x64"
        MACARM = "mac-arm64"

    class Firefox(Enum):
        """
            Firefox web driver architecture
        """

        WINX86_32 = "win32"
        WINX86_64 = "win64"
        WINARM = "win-aarch64"

        LINUXX86_32 = "linux32"
        LINUXX86_64 = "linux64"
        LINUXARM = "linux-aarch64"

        MACX86_64 = "macos"
        MACARM = "macos-aarch64"

    class Edge(Enum):
        """
            Edge web driver architecture
        """

        WINX86_32 = "win32"
        WINX86_64 = "win64"
        WINARM = "arm64"

        # LINUX86_32 : no support for linux 32bit
        LINUXX86_64 = "linux64"
        # LINUXARM : no support for linux arm64

        MACX86_64 = "mac64"
        MACARM = "mac64_m1"


class WebDriverName:
    """
        Web driver name
    """

    def __init__(
        self,
        driver_type: WebDriverType
    ):

        self.driver_type = driver_type


    def __str__(
        self
    ) -> str:

        match self.driver_type:
            case WebDriverType.CHROME:
                return "chromedriver"
            case WebDriverType.FIREFOX:
                return "geckodriver"
            case WebDriverType.EDGE:
                return "msedgedriver"
            case _:
                raise ValueError(f"不受支持的 web driver 类型 : {self.driver_type}")


class WebDriverExecName:
    """
        Web driver executable file name
    """

    def __init__(
        self,
        driver_type: WebDriverType,
        arch: WebDriverArch
    ):

        self.driver_type = driver_type
        self.arch = arch


    def __str__(
        self
    ) -> str:

        is_win = True if self.arch is WebDriverArch.Chrome.WINX86_32 or\
            self.arch is WebDriverArch.Chrome.WINX86_64 or\
            self.arch is WebDriverArch.Firefox.WINX86_32 or\
            self.arch is WebDriverArch.Firefox.WINX86_64 or\
            self.arch is WebDriverArch.Edge.WINX86_32 or\
            self.arch is WebDriverArch.Edge.WINX86_64 else False
        match self.driver_type:
            case WebDriverType.CHROME:
                return f"{WebDriverName(self.driver_type)}" + (".exe" if is_win else "")
            case WebDriverType.FIREFOX:
                return f"{WebDriverName(self.driver_type)}" + (".exe" if is_win else "")
            case WebDriverType.EDGE:
                return f"{WebDriverName(self.driver_type)}" + (".exe" if is_win else "")
            case _:
                raise ValueError(f"不受支持的 web driver 类型 : {self.driver_type}")


class WebDriverFileName:
    """\
        Web driver compressed file name
    """

    def __init__(
        self,
        version: str,
        driver_type: WebDriverType,
        arch: WebDriverArch
    ):

        self.version = version
        self.driver_type = driver_type
        self.arch = arch

    def __str__(
        self
    ) -> str:

        match self.driver_type:
            case WebDriverType.CHROME:
                return f"{WebDriverName(self.driver_type)}-{self.arch.value}.zip"
            case WebDriverType.FIREFOX:
                if self.arch is WebDriverArch.Firefox.WINX86_32 or\
                    self.arch is WebDriverArch.Firefox.WINX86_64:
                    suffix = "zip"
                else:
                    suffix = "tar.gz"
                return f"{WebDriverName(self.driver_type)}-v{self.version}-{self.arch.value}.{suffix}"
            case WebDriverType.EDGE:
                return f"edgedriver_{self.arch.value}.zip" # Edge web driver file name is different
            case _:
                raise ValueError(f"不受支持的 web driver 类型 : {self.driver_type}")


class WebDriverURL:
    """
        Web driver download URL
    """

    def __init__(
        self,
        version: str,
        driver_type: WebDriverType,
        arch: WebDriverArch
    ):

        self.version = version
        self.driver_type = driver_type
        self.arch = arch
        self.file_name = str(WebDriverFileName(self.version, self.driver_type, self.arch))


    def __str__(
        self
    ) -> str:

        match self.driver_type:
            case WebDriverType.CHROME:
                return f"https://storage.googleapis.com/chrome-for-testing-public/"\
                       f"{self.version}/"\
                       f"{self.arch.value}/"\
                       f"{self.file_name}"
            case WebDriverType.FIREFOX:
                return f"https://github.com/mozilla/geckodriver/releases/download/"\
                       f"v{self.version}/"\
                       f"{self.file_name}"
            case WebDriverType.EDGE:
                return f"https://msedgedriver.microsoft.com/"\
                       f"{self.version}/"\
                       f"{self.file_name}"
            case _:
                raise ValueError(f"不受支持的 web driver 类型 : {self.driver_type}")


class WebDriverDownloader:
    """
        Base class for WebDriver downloaders

        Args:
            driver_type (WebDriverType): Web driver type
            version (str): WebDriver version
            arch (WebDriverArch): WebDriver architecture
            download_dir (str): Download directory
    """

    def __init__(
        self,
        driver_type: WebDriverType,
        driver_version: str,
        driver_arch: WebDriverArch,
        download_dir: str
    ):

        self.driver_type = driver_type
        self.arch = driver_arch
        self.version = driver_version
        self.download_url = str(WebDriverURL(self.version, self.driver_type, self.arch))
        self.download_dir = Path(download_dir)/self.driver_type.value/self.version/self.arch.value
        self.download_dir.mkdir(mode=0o0755, parents=True, exist_ok=True)
        self.download_path = self.download_dir/str(WebDriverFileName(self.version, self.driver_type, self.arch))


    def download(
        self,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> Optional[Path]:

        try:
            # downlaod file : 0% - 98%
            if not self._download(progress_callback):
                return None
            # verify file : 98% - 99%
            if not self._verify(progress_callback):
                return None
            # extract file : 99% - 100%
            driver_path = self._extract(progress_callback)
            if not driver_path:
                return None
            return driver_path
        except Exception:
            return None


    def _download(
        self,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
        max_retries: int = 3
    ) -> bool:

        CHUNK_SIZE = 8192*8 # 64KB chunk
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate'
        }

        for attempt in range(max_retries):
            try:
                # resume download if file exists
                if self.download_path.exists():
                    downloaded_size = self.download_path.stat().st_size
                    headers_ = headers.copy()
                    headers_['Range'] = f"bytes={downloaded_size}-"
                    mode = 'ab'
                else:
                    downloaded_size = 0
                    headers_ = headers
                    mode = 'wb'
                # get response
                response = requests.get(str(self.download_url), headers=headers_, stream=True, timeout=120)
                if response.status_code not in [200, 206]:
                    if self.download_path.exists():
                        self.download_path.unlink()
                    downloaded_size = 0
                    mode = 'wb'
                    response = requests.get(str(self.download_url), headers=headers, stream=True)
                response.raise_for_status()
                # get total size
                total_size = int(response.headers.get('Content-Length', 0))
                if response.status_code == 206:  # Partial Content - server supports Range
                    total_size += downloaded_size
                # download file with progress callback and speed calculation
                start_time = time.time()
                last_time = start_time
                last_size = downloaded_size
                last_progress = 0.0
                with open(self.download_path, mode) as f:
                    for chunk in response.iter_content(CHUNK_SIZE):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if not progress_callback or total_size == 0:
                            continue
                        current_time = time.time()
                        current_progress = (downloaded_size/total_size)*98.0
                        if current_progress - last_progress >= 1.0 or current_progress == 98.0:
                            elapsed = current_time - last_time
                            if elapsed > 0:
                                speed = (downloaded_size - last_size)/elapsed/1024.0  # KB/s
                            else:
                                speed = 0.0
                            progress_callback(current_progress, 100, speed, "下载中...")
                            last_progress = current_progress
                            last_size = downloaded_size
                            last_time = current_time
                if total_size > 0 and self.download_path.stat().st_size < total_size:
                    raise Exception(f"下载不完整 : {self.download_path.stat().st_size}/{total_size} 字节")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    progress_callback(0, 100, 0.0, "准备重试...")
                    time.sleep(1)
                    continue
                raise e


    def _verify(
        self,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> bool:

        progress_callback(98, 100, 0.0, "验证完成")
        return True


    def _extract(
        self,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> Optional[Path]:

        try:
            progress_callback(98, 100, 0.0, "解压中...")
            file_path_str = str(self.download_path)
            if file_path_str.endswith('.tar.gz'):
                with tarfile.open(self.download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.download_dir)
            else:
                with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                    zip_ref.extractall(self.download_dir)
            driver_file = None
            for root, _, files in os.walk(self.download_dir):
                for file in files:
                    expected_name = str(WebDriverExecName(self.driver_type, self.arch))
                    if file == str(expected_name):
                        src_path = Path(root, file)
                        dst_path = self.download_dir/file
                        src_path.rename(dst_path)
                        driver_file = dst_path
                        break
                if driver_file:
                    break
            if not driver_file:
                raise FileNotFoundError(f"未找到 web driver 文件 : {expected_name}")
            progress_callback(100, 100, 0.0, "解压完成")
            self.download_path.unlink()
            self._cleanup(driver_file)
            return driver_file
        except Exception:
            return None


    def _cleanup(
        self,
        driver_file: Path
    ) -> None:

        for item in self.download_dir.iterdir():
            if item != driver_file:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()


class ChromeDriverDownloader(WebDriverDownloader):
    """
        Chrome web driver downloader

        Only support version higher than 114
    """

    def __init__(
        self,
        version: str,
        arch: WebDriverArch,
        download_dir: str
    ):

        super().__init__(WebDriverType.CHROME, version, arch, download_dir)


class FirefoxDriverDownloader(WebDriverDownloader):
    """
        Firefox web driver downloader

        This class do not resolve version mapping,
        only support driver version higher than 0.17.0
    """

    def __init__(
        self,
        version: str,
        arch: WebDriverArch,
        download_dir: str
    ):

        super().__init__(WebDriverType.FIREFOX, version, arch, download_dir)


class EdgeDriverDownloader(WebDriverDownloader):
    """
        Edge web driver downloader
    """

    def __init__(
        self,
        version: str,
        arch: WebDriverArch,
        download_dir: str
    ):

        super().__init__(WebDriverType.EDGE, version, arch, download_dir)
