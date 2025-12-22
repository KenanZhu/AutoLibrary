
# AutoLibrary
---

![AutoLibrary Logo](./src/gui/icons/AutoLibrary_128x128.ico)

![License](https://img.shields.io/github/license/KenanZhu/AutoLibrary)
![Issue](https://img.shields.io/github/issues/KenanZhu/AutoLibrary)
![Release](https://img.shields.io/github/v/release/KenanZhu/AutoLibrary)
![Download](https://img.shields.io/github/downloads/KenanZhu/AutoLibrary/total)

了解更多请访问 [_AutoLibrary 网站_](http://autolibrary.cv)

---

### 功能

1. 自动预约 - 支持自动预约
2. 自动续约 - 支持自动续约
3. 自动签到 - 支持自动签到
4. 批量操作 - 支持同时预约多个用户，可以指定当前需要跳过的用户，并将用户分成多个组
5. 定时任务 - 使用内置定时任务管理，添加定时任务，指定时间后按当前预约信息自动运行

_1,2,3 的具体操作方法和注意事项请访问网站 [帮助手册](https://autolibrary.cv/docs/manual_lists.html)_

### 特点

#### 关于预约等操作的注意事项

工具会自动处理登录过程的验证码识别过程，正常情况下单次识别准确率在 90% 以上，如遇验证码识别错误，大概率是校园网网络环境不佳导致的。

只要确保处于校园网网络环境内，工具都是可以正常运行的。操作处理速度基本上取决于校园网的网络环境，一般情况下在 3-4 秒左右即可完成一个用户的操作，完全满足正常使用需求。

> [!NOTE]
> 工具仅作为正常的预约，签到和续约的图书馆辅助工具，请勿干扰图书馆的正常运行（如故意预约多个座位，或同时预约大量的用户等，对此影响图书馆正常运行本工具概不负责，请在善用工具方便自己的情况下尽量不用影响其他同学的使用）。

#### 关于批量操作的注意事项

批量操作时，建议将需要操作的用户分成多个组，每个组的用户数量不要超过 4 人（即一整张桌子的数量），否则会影响操作效率，大量用户同时预约会一定程度上增加图书馆服务器的压力，影响正常使用。根据需要在用户管理界面中可以勾选本次操作是否跳过该用户，以提高运行效率。

#### 关于定时任务的注意事项

定时任务会在指定的时间自动运行，运行时会根据当前预约信息进行操作。一般情况下不建议设置两个运行开始时间比较接近的定时任务，否则后一个任务会等待前一个任务完成后才会运行，按照队列的顺序执行。

### 如何使用

1. 下载最新版本的 AutoLibrary 工具压缩包，[点击这里](https://github.com/KenanZhu/AutoLibrary/releases)。
2. 解压下载的文件到任意目录。
3. 运行 `AutoLibrary.exe` 文件。
4. 按照提示操作即可。

#### 平台支持 & 编译步骤

本工具目前仅支持 Windows 平台，由于使用 PySide6 库开发，理论上是可以自行编译并在 Linux 和 macOS 上运行，这里提供简单的编译步骤：

1. 确保系统安装了 Python 3.13 或以上版本。
2. 安装 pyside6 selenium ddddocr 库，命令为 `pip install pyside6 selenium ddddocr`。
3. 在 `src/gui/batchs` 目录下运行 `complie_ui.bat` （linux 和 macOS 系统使用 `complie_ui.sh`） 文件来编译 Qt 的 UI 文件。
4. 在上一步相同目录内运行 `complie_rc.bat` （linux 和 macOS 系统使用 `complie_rc.sh`） 文件来编译 Qt 的资源文件。
5. 待上述步骤完成后，运行 `src/Main.py` 文件即可。

*注意 1*：如果 python 使用的是虚拟环境，请在虚拟环境安装依赖后，在激活的虚拟环境终端中使用 `cd src/gui/batchs` 命令切换到 `batchs` 目录下，再运行编译脚本。否则会提示缺少必要的 Qt PySide 依赖库。

*注意 2*：由于 ddddocr 的代码版本问题，其中的 `__init__.py` 文件中的函数 `def classification(self, img: bytes):` 中的 `image.resize` 方法传入了不符合当前版本的`resample` 参数，导致在 Python 3.13 以上中运行时会报错。请将 `image.resize` 方法中的参数替换为 `resample=Image.Resampling.LANCZOS`，具体函数如下：
```python
def classification(self, img: bytes):
        image = Image.open(io.BytesIO(img))
        image = image.resize((int(image.size[0]*(64/image.size[1])), 64), Image.Resampling.LANCZOS).convert('L')
                                                                              ^^^^^
                                                                     请将上述参数替换为如上所示的 `Image.Resampling.LANCZOS`

        ...
```

### Q&A

#### 为什么开发这个工具？

其实是因为自己在使用图书馆时，发现预约和续约等操作比较麻烦，图书馆的登录系统也比较老旧，验证码错误后需要重复输入。有时候网络环境不好的时候，登录很慢，想赶紧签到或者预约明天的座位，而且会有朋友让我帮忙预约一个座位，这时候就需要一个工具来帮助自己快速完成这些操作，自己则不需要管这些事情，只需要专注自己的事情就可以了。

#### 工具后续会收费吗？

不会，本工具完全免费使用，也不会有任何收费项，如果你觉工具对你有帮助，可以为我捐助一瓶可乐的价格，以用于 AutoLibrary 网站的维护和软件的稳定更新。

#### 会有手机端的版本吗？

暂时没有考虑，而且也没有足够的能力和精力开发多平台的版本并维护，所以暂时只提供 Windows 版本。

#### 后续会有哪些功能？

由于本人的时间和精力有限，开发后续功能会有所取舍，如果你有什么功能建议或者想参与开发，欢迎联系我。

首先当前 1.0.0 版本的功能对于正常使用已经足够，不过会考虑后续着重完善 2-4 预约时的操作流程，暂时由以下构想：

1. 2-4 人一起预约时，往往会偏向于预约并排或对面的整个空座位，这时候工具会按照一定策略查询搜索符合条件的座位，并预约并排或对面的整个座位，而不是各自独立预约。
2. 预约时会考虑到组内用户的预约时间是否冲突，若冲突则会提示用户是否继续预约，若用户选择继续预约，则会按需要调整预约时间，再进行预约。
3. 对于比较固定的用户，会考虑在定时任务管理中添加如 ‘每日任务’ ‘每周任务’ 等选项，用户可以根据需要设置定时任务重复的日期范围，自动完成预约，签到，续约等操作。

不过以上功能的实现，需要一定的时间和精力测试与调试，也需要考虑到图书馆的正常运行，所以暂时不会着手开发，也许会进行一些小的功能验证。

#### 其他功能建议？

如果有其他功能建议，或者遇到了什么功能性，操作上的问题，欢迎联系我。

如果你有足够的开发能力，可以 Fork 本项目，根据自己的需求进行修改和完善，也欢迎提交 Pull Request 到本项目。

### 联系我

- 项目维护：[KenanZhu (Nanoki)](https://github.com/KenanZhu)
- 电子邮箱：<nanoki_zh@163.com>

_**Free to use** —— AutoLibrary 是一个基于 MIT 协议免费开源的工具_
