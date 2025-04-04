<h1 align="center">
  <a href="https://github.com/maplelost/lazy-eat/releases">
    <img src="https://github.com/maplelost/lazy-eat/blob/master/public/lazyeat.png?raw=true" width="150" height="150" alt="banner" /><br>
  </a>
<div align="center">

![GitHub stars](https://img.shields.io/github/stars/maplelost/lazyeat)
![GitHub forks](https://img.shields.io/github/forks/maplelost/lazyeat?style=flat)

[English README](README_EN.md)

</div>
</h1>

# 修改说明

原项目很有趣，但是由于我的笔记本摄像头离我太近，在鼠标移动时经常会离开识别范围，而且一直竖着食指也很累，所以我在原项目的基础上修改了一下操作逻辑，使用状态机不同状态控制鼠标的不同行为使其更贴近我的使用习惯。
如果你感兴趣可以试着用一下，安装包放release了。

[原项目地址](https://github.com/maplelost/lazyeat)

UI界面中的操作指引我没改，所以在这里简单说明一下操作
修改后的操作逻辑：
1. 每个操作状态都从等待手势，也就是举起一只手掌开始，举起手掌后程序开始等待具体的指令，这部分手势和原项目几乎一致，一根食指切换到移动模式，三指切换到滚轮模式……，在移动模式可以通过拇指与中指、无名指的距离控制左右键。
2. 摇杆操作逻辑：摇杆控制点（屏幕上的小红圈）在大圈内时是直接控制模式，位移量与手指的移动距离成正比，圈外时是摇杆模式，会持续移动，移动速度与小圈和大圈的距离成正比。
3. 移动模式和滚轮模式会一直保持，直到识别到等待手势指令，这时候就会回到1的状态等待指令。
4. 在移动模式中通过食指指尖的位置来控制鼠标移动，鼠标移动方式见第二条。左右键操作用拇指，中指，无名指控制，拇指和中指靠近时左键按下，离开时左键松开，无名指和中指靠近时右键按下，离开时右键松开。按下和松开的状态通过蓝色的圈来表示，蓝色的圈越靠近红色的圈代表手指距离越近，蓝色圈消失时代表按键按下，蓝色圈重新出现时代表按键松开。
5. 滚轮模式下，当食指和拇指指尖靠近，蓝色圈消失时就可以用轮盘控制滚轮，蓝色圈出现时滚轮停止。
6. 语音，基本和原项目一致，识别到6就一直进入语音识别状态。**但是停止语音识别的手势改为了等待手势**
7. 其他功能，其他功能都是一次性操作，没有状态持续的必要，因此在1状态下直接可以触发。
8. 退出等待，等待状态持续5秒后会自动退出。


# 🍕 Lazyeat

Lazyeat 吃饭时看剧/刷网页不想沾油手？

对着摄像头比划手势就能暂停视频/全屏/切换视频！

如果你觉得对你有用的话，不妨给我一个 star⭐ 吧~

如果有任何的想法或者建议，都可以在 [Discussions](https://github.com/maplelost/lazyeat/discussions) 中讨论喔！

# 🌠 截图

视频演示:https://www.bilibili.com/video/BV11SXTYTEJi/?spm_id_from=333.1387.homepage.video_card.click

![img.png](.readme/img.png)

# 📢 语音识别模型下载

[小模型](https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip)

[大模型](https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip)

下载后解压到 `exe` 同级的 `model` 文件夹下,才能使用语音识别功能

![img.png](.readme/img_model_example.png)

# 📝 TODO

- [ ] (2025 年 3 月 12 日) 嵌入 browser-use ，语音控制浏览器
- [ ] (2025 年 3 月 24 日) 开发安卓版本

[//]: # "# 📚 References"

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=maplelost/lazyeat&type=Date)](https://www.star-history.com/#maplelost/lazyeat&Date)

# 开发问题

tauri build 失败:[tauri build 失败](https://github.com/tauri-apps/tauri/issues/7338)

cargo 被墙:[cargo 被墙,换源](https://www.chenreal.com/post/599)

```
# 不知道有没有用
rm -rf ~/.cargo/.package-cache 
```


