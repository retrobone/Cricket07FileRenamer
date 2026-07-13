# Cricket 07 File Renamer
Program that renames MD5-hashed filenames of Cricket 07 to proper filenames.<br>

## Usage

Run and select source directory and run the program, maps files in proper name format, files that still remain and in hashed format can be detailed

<ul>
  <li>Renames with the help of <a href="github.com/retrobone/Cricket07ReDir">Cricket 07 ReDir</a> and various syntaxes dynamically</li>


<li>These renamed files can be then used with <a href="github.com/retrobone/Cricket07FileLoader">Cricket 07 File Loader</a></li>
</ul>

## Guide for using patches with Ultimate ASI Loader
<ol>
  <li>
    For loading different patches from the game folder, use <a href="https://github.com/ThirteenAG/Ultimate-ASI-Loader/releases"> Ultimate ASI Loader, (ddraw.dll x32)</a>
  </li>
  <li>
    Then create global.ini in the main game folder and <a href="https://raw.githubusercontent.com/ThirteenAG/Ultimate-ASI-Loader/refs/heads/master/data/scripts/global.ini">copy contents from here</a>
  </li>
  <li>
    Go the the OverloadFromFolder line and add your patch folder name, if multiple patche folders, segregate by "|"
  </li>
  <ul>
    Example- OverloadFromFolder=WC2011 | IPL2011
  </ul>
</ol>
  <li>Also - <a href="https://github.com/ThirteenAG/Ultimate-ASI-Loader#update-folder-overload-from-folder">Guide about Update Folder from Ultimate-ASI-Loader repo</a></li>
</ul>
