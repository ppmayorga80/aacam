# aacam

**ASCII Art Camera** — Convert images, videos, or live webcam feeds into real-time ASCII art in your terminal (`ncurses`) or stream the output to a virtual camera (OBS Studio).

You can customize the output scale, zoom, pan, font (monospaced TTF), and character set (ordered from low to high visual density).

## Installation

### 1. Set up OBS Studio *(Optional — required only for virtual camera output)*
1. Download and install [OBS Studio](https://obsproject.com/).
2. Open OBS Studio and click **Start Virtual Camera** in the **Controls** dock, then click **Stop Virtual Camera**. *(This registers the virtual camera device on your system.)*
3. Close OBS Studio.

### 2. Clone the repository
```bash
git clone [https://github.com/ppmayorga80/aacam.git](https://github.com/ppmayorga80/aacam.git)
cd aacam
```

### 3. Create a virtual environment and install dependencies
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

* **Windows (PowerShell):**
  ```powershell
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### 4. Run the application
Ensure your virtual environment is activated, then run `python src/aacam.py` followed by your desired arguments.

> **Note:** For brevity, the examples below use `aacam` as shorthand for `python src/aacam.py`.

## Command-Line Options

| Command | Description |
| :--- | :--- |
| `aacam --help` | Display help and all available arguments |
| `aacam -i "lena.png"` | Display the image `lena.png` in the terminal |
| `aacam -i "video1.mp4"` | Play the video `video1.mp4` in the terminal |
| `aacam -i 0` | Display webcam `0` in the terminal |
| `aacam -i 0 -o 0` | Stream webcam `0` to virtual camera `0` |
| `aacam -i "lena.png" -c min` | Render `lena.png` using the minimal (`min`) character set |
| `aacam -i "lena.png" -s 0.5` | Render `lena.png` with a scale factor of `0.5` |

> **Tip:** Route `aacam` to a virtual camera (`-o 0`) to use your ASCII feed as a webcam in Zoom, Google Meet, Microsoft Teams, or any other video conferencing app.

## Keyboard Controls

While `aacam` is running, use the following keys to adjust the view in real time:

* **`+` / `-`**: Zoom in / Zoom out
* **Arrow Keys**: Pan the viewport (step size: `1`)
* **`W` `A` `S` `D`**: Pan Up, Left, Down, Right (step size: `10`)

## Example Output

Render a single image using the `sym` character set:

```bash
aacam -i "lena.png" -c sym
```

<pre style="background-color: #000000; color: #ffffff; padding: 16px; border-radius: 6px; overflow-x: auto; line-height: 1.15;">
##***##*;======+++++++++++*+++++*++++++==*#**#*****&$==+++++++=*
****###*=;=====++++++++++++++++++++++++===*#*#*#****&$=++=++++;-
*######*=;=====+++++++++++++++++++++++++==+*####*****&$+==++;---
###**##*;;=====+++++++++++*##%%+=+++++++==+***********&$*=:-----
##*;*##*;;;=====++++*+++++*###%%&&&=======+************&$-------
#+;;*##*;;;====+++++==+++++*###%%%&$&$;===+**+;+*******-------;;
=;;;*##*;;;==;==++==+=+*+****%#&&&&&&&$;:;+***:-+*****.-:---:;**
;;;;*##*;;;;====*===+=+++*+*%%%%&&&&&&&&$:+***;-.;$#=------.*+##
;;;;*##*;;;;====#===++++=##%%#%%%%&&&&&&&&=***-&#&&&$------**##*
====*##*;;;;;==+#====+=*++**######%#%%%%%%%#&%&&&&&$+----;*#*#**
;;;;*##*;;;;;==$#*=;;+++****###*#*########&&%&&&&*+&.:--+*##*##*
=;==*##*;;;===;$%+*++=++++*++=**++*=-##&%%%&&&&&;;&.---+*##*****
====*##*;;;====:%*+;+=+++++-:-=--.-#&%%%%%%&=+*#%---.:=*#####***
==;;*###;;;;;===;%=+++++:;--.-:-;+%%%%#%%&*:;+%------:+#######**
===;*###;;;;=====$==+;:;--::-..=##%###%&&&&;-=:--:---+#**####***
=;=;*#%#;;==;==++;++;.::--.--=##%%*##%%%&&&#--*-::--**####******
;==;*###=;;=;==**#;--;=-;--.+#%&=;=;++*%%+:::-#-:--++****#******
=;;:*#%#=;;==-#&-=-;=-::..:%%%=+==&*++*$+;#---#;---*#**#*****++#
;;;:+#%#=;===*-===-;+#---=%&;+*#####+++$%*+=-:#---********++%&%%
:::-*###=;=+-;-:+----;+-;%#:=+**####+++&#*+=-;=*-;+#******+%%%&&
;;:-+###=+=;;:*=#----=-##:-=;++***#*+++##*+--;-*.*#******+&%&&&&
:::;*###=;=;:-:;=*;:-#;%---==++*******%%*+---:.#=********#%&&&&&
--:;*#%#==*--:-;=*-+&;--:-;;:+++*+====++*---;:-**#******+%&&&&&&
---;*###=;;:--=;=;:=%--:-::-:;=+++++****----;:;+********+&&$&&&&
---=*#%#==-::--:;=++-------:::-::=+*#**-----=:-********++$&&&&%:
+;:-=##%=%.-.==+:-==#:--------;++++**#%%&&;.=::#**++=;;=*&&&*-:;
:+#:=####.-:-;-;=:=*=;=-:-:-:=;=+*+**##%%&&$+-:*****++++&&&;=;=;
.;#;=#%%#---.*-:-;=-=+#-:---;+;++++***##%%&&&*.****+++%&$&=;==;=
.-#=;#%#*----:::.;;+=-.:::-;+==+**+***###%&&&&-***++++&&&+=;;;=;
.-#*;###+;--:-;--:+:-;.---;++;+********###%&&&$::;=+**+&%;;:=;=;
;=##;#%%;---:-:--:-:+--.-;=-=+++****+***##%%&&&:==;:-&%#-;;;;=;:
</pre>

After zoom in and applying panning:
<pre style="background-color: #000000; color: #ffffff; padding: 16px; border-radius: 6px; overflow-x: auto; line-height: 1.15;">
~~~-~~--,:,,,::,--~~~:,,+.~x=;=$$$$$XXXXXXXXXXX$$$$$$X:,-;~:+;;+x=xxXXX$=,,,
-~:-,,,-;,,,,::,-,-,--,+-+~;x$$$$$XXXXXXXXxXXXXXXXX$$X+~~;~::=;;+=xX$$-,,,,,
~:~--,,~~,-;,-,,-~--~~-;:==X$XXXXXXXXXXXXXXXXXX$$$$$$$x=::-+~~=++=x+-,,,,,,-
-~-~~----+:,,,,-,,,,-+~:x+XxXXX$XXxXXXXxXXxX$$$$$$$$$$Xx;:-,::~=+==;,,,,,,--
,~~-~-,~,,;;:~,,.,,x;:Xx=XXX$$$XxxxxXXxxXXX$$$$$$$$$$$$X+:~,,-~~=xx:,,,,,,--
,-,---~~-,-;,,..,==;xXxx+xxxXXXXXxxX=xxxXX$$$$$$$$&&&&&$x+:-,,~~=xx~--,-----
,-,,-,~:~:~x;..+x;=XXXXX=xxX$$xXxx=xxxxXX$$$$$$$$$&&&&&$X=~~,,,--xX:-,------
-,,~-,,,~,.,+~x;+xxXX$XXx+X$xxxxxxxxXXXXXX$$$$&$&$&&&&&&$x::-,,,:+X:,-,-----
-,-,,:-,;,,,+::Xxxxxx$X$XXXxxxxxxxxXXXXXXX$$$$$$$$$$&&&&&X;:-,,,~~X=---~----
-,~,,;,:,.-x:=XxXXx=x$$$X=~:;;++==xXXXXXXXX$$$$$$$$$$&&&Xx;-,,,,-,Xx--~---~~
,,-:;,-,,+=;$xXX$x=xX$X;====x=+:~--~+xXXXXXX$$$X$$$$Xx;:-~::~,,,--Xx;--~~---
,,,,,-.-x;XxxX$$XXX$::::~-~-~:,~;+++;;+=xxxX$$$$$X=++:~--~~~-~,,-~xX;:,-----
;,,,,.~=:$xXX$$$$$:--,-,,,,,-;~,,,:++++===xX$$&$x~----:-,----,,,,-=X::----,,
,--,~;==$XXX$$$$+:~---:::~,;-$$$:~;:;;++==xX&&$;---,-;Xx~-~,-,,,--+X;:-~--,-
,.,-;~+xxX$$$$x;;+++;,:;;~~+$$$$=+;+;+++==X$&&+;=;~:~xXx~-,,,,,,~-;x+-::--,-
,,.x:XXxX$$$=;;+=+===+++;+++=xxxXX=++;+++=X$#&Xx=+=+xx;:,-~---~-~,~x=::~-,,,
.-=:=xXX$$x~:++================xx=x+++++++xX&#Xxx=++++:;;::--,,,~,~=x+--,,,,
-=:xxX$&$-:;;++===xxxxxXxxxxxXxXxx=+==++++xX&#$Xxxx=+++;;;:--,,-~,-xX=-~-,,-
x:+X$$&-,~:;+++===xxxXXXxXXXxXXXxx====++++=X&#$XXX====+++;;~-,--~,,xXx,-,,,-
;xXX$X,--:;++++====xxXXXXXXXXXxXxx=====+++=x&#&Xxxxx==++++:--,--~,,=x=--,-,,
+X$&=,-,-:;+++=+=====xxxXXXXxXxxx=====++++=x$&&Xxxx===++++~-,-,,~,,+X++,,---
&&&,,,-,-::;+++++====xxxXxXXxXxx==+++++++++xX&&&xxx===+++;-,,---:,,:x+=~,--,
&x,,,,~-~:;;++++======xxxxxxxxxx==+++++++++=X$#&=x====++;:,,-,-~~,,~xx=:,,--
x-,,,,:-~~:;;++++======x=xxxxxx===;;+===+++=XX##=====+++;-,,,,~~~-,,=xx+-.,;
,..,,,::~::;+++++=========xxxxx===;+++;+++++=X&&======+;,,,,,-~--,,,=x=+,.,+
,,,,,,::~:;;;+++++=======xxxxxxx==+;+++++;:++xXXx===++;-,-,,,-~-~,-,:x==~,:=
,~-,,,::~:;+++++++=========xxxxxxx===++=x=x$$$Xx====++,,,-,,-~~~-,,,-===:-+=
,,-,,,~;:;;;++++++============xx=======x&$x$$$Xx===++--,,,,--~~~--,,,;x=:;==
,-~-,,-:+:;;++++++=====+============xxxX&$xX$$Xx===+-,,,,,--~~~~,-,,,;X;~+==
--~-,,-~;~:;+++++++=======++++============x===x++==:,,-,,,---~~~---,,-x;:===
---~,,,-~~~;;+++++++======;;:~~:::;;::::;;;;:;++==-,,,-,,----:~~-,~,,-x=====
</pre>