#!/opt/homebrew/bin/python3

### App Store Screenshot Generator
# Created by Zachary Morden

## External Dependencies:
# PIL (Python Image Library using the Pillow fork https://pillow.readthedocs.io/en/stable/installation.html)

import io, os, sys, base64, json, urllib.request, textwrap
from PIL import Image, ImageDraw, ImageFont
from string import ascii_letters

## Configuration: Start

# This table is used to determine the hierarchial key path for a specified device in the frames JSON.
frameDataLookupTable = {
  "iPhone13ProMaxPortrait":  ("iPhone", "12-13", "Pro", "Portrait"),
  "iPhone13ProMaxLandscape": ("iPhone", "12-13", "Pro Max", "Landscape"),
  "iPhone13ProPortrait":     ("iPhone", "12-13", "Pro", "Portrait"),
  "iPhone13ProLandscape":    ("iPhone", "12-13", "Pro", "Landscape"),
  "iPhone13Portrait":        ("iPhone", "12-13", "Pro", "Portrait"),
  "iPhone13Landscape":       ("iPhone", "12-13", "Pro", "Landscape"),
  "iPhone13MiniPortrait":    ("iPhone", "12-13", "mini", "Portrait"),
  "iPhone13MiniLandscape":   ("iPhone", "12-13", "mini", "Landscape"),

  "iPhone8Portrait":         ("iPhone", "iPhone 8 and 2020 SE", "Portrait"),
  "iPhoneSEPortrait":        ("iPhone", "iPhone 8 and 2020 SE", "Portrait"),
  
  "iPhone12ProMaxPortrait":  ("iPhone", "12-13", "Pro Max", "Portrait"),
  "iPhone12ProMaxLandscape": ("iPhone", "12-13", "Pro Max", "Landscape"),
  "iPhone12ProPortrait":     ("iPhone", "12-13", "Pro", "Portrait"),
  "iPhone12ProLandscape":    ("iPhone", "12-13", "Pro", "Landscape"),
  "iPhone12Portrait":        ("iPhone", "12-13", "Pro", "Portrait"),
  "iPhone12Landscape":       ("iPhone", "12-13", "Pro", "Landscape"),
  "iPhone12MiniPortrait":    ("iPhone", "12-13", "mini", "Portrait"),
  "iPhone12MiniLandscape":   ("iPhone", "12-13", "mini", "Landscape"),

  "iPhone11ProMaxPortrait":  ("iPhone", "11", "Pro Max", "Portrait"),
  "iPhone11ProMaxLandscape": ("iPhone", "11", "Pro Max", "Landscape"),
  "iPhone11ProPortrait":     ("iPhone", "11", "Pro", "Portrait"),
  "iPhone11ProLandscape":    ("iPhone", "11", "Pro", "Landscape"),
  "iPhone11Portrait":        ("iPhone", "11", "11", "Portrait"),
  "iPhone11Landscape":       ("iPhone", "11", "11", "Landscape"),

  "iPadMini2021Portrait":    ("iPad", "2021 iPad mini", "Portrait"),
  "iPadMini2021Landscape":   ("iPad", "2021 iPad mini", "Landscape"),
  "iPad2021Portrait":        ("iPad", "2021 iPad", "Portrait"),
  "iPad2021Portrait":        ("iPad", "2021 iPad", "Landscape"),
  "iPadPro201811Portrait":   ("iPad", "2018-2021 iPad Pro 11", "Portrait"),
  "iPadPro201811Landscape":  ("iPad", "2018-2021 iPad Pro 11", "Landscape"),
}

# This lookup table can be updated for more devices in the past, present, or future by finding their physical width and height.
# A good site to find this information is "iOS Resolution:" https://www.ios-resolution.com/
frameDimensionsLookupTable = {
  "iPhone13ProMaxPortrait":  (1284, 2778),
  "iPhone13ProMaxLandscape": (2778, 1284),
  "iPhone13ProPortrait":     (1170, 2532),
  "iPhone13ProLandscape":    (2532, 1170),
  "iPhone13Portrait":        (1170, 2532),
  "iPhone13Landscape":       (2532, 1170),
  "iPhone13MiniPortrait":    (1170, 2532),
  "iPhone13MiniLandscape":   (2532, 1170),

  "iPhone8Portrait":         (750, 1334),
  "iPhoneSEPortrait":        (750, 1334),

  "iPhone12ProMaxPortrait":  (1284, 2778),
  "iPhone12ProMaxLandscape": (2778, 1284),
  "iPhone12ProPortrait":     (1170, 2532),
  "iPhone12ProLandscape":    (2532, 1170),
  "iPhone12Portrait":        (1170, 2532),
  "iPhone12Landscape":       (2532, 1170),
  "iPhone12MiniPortrait":    (1170, 2532),
  "iPhone12MiniLandscape":   (2532, 1170),

  "iPhone11ProMaxPortrait":  (1242, 2688),
  "iPhone11ProMaxLandscape": (2688, 1242),
  "iPhone11ProPortrait":     (1125, 2436),
  "iPhone11ProLandscape":    (2436, 1125),
  "iPhone11Portrait":        (828, 1792),
  "iPhone11Landscape":       (1792, 828),

  "iPadMini2021Portrait":    (1488, 2266),
  "iPadMini2021Landscape":   (2266, 1488),
  "iPad2021Portrait":        (1620, 2160),
  "iPad2021Portrait":        (2160, 1620),
  "iPadPro201811Portrait":   (1668, 2388),
  "iPadPro201811Landscape":  (2388, 1668),
}

framesPath = "temp/frames.json"
inputDir = "Raw Shots/"
outputDir = "Composited Shots/"
tempDir = "temp/"
fontDirs = ["/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]

backgroundColor = (79, 159, 241) # Jean purple.
textColor = (255, 255, 255) # White.
textMultilineSpacing = 10
frameScaleFactor = 0.7 # Relation between the width of the final image and the size of the device frame.
frameVerticalPaddingFactor = 0.05 # Relation between the bottom of the device frame and the bottom of the final image relative to the final image's height.
maximumLineWidthPercentage = 0.9
multilineTextAlignment = "center"

screenshots = { }

## Configuration: END

## Args: START

if sys.argv.__contains__("--background-color"):
  index = sys.argv.index("--background-color") - 1
  colors = sys.argv[index].split(":")
  backgroundColor = (int(colors[0]), int(colors[1]), int(colors[2]))

if sys.argv.__contains__("--text-color"):
  index = sys.argv.index("--background-color") - 1
  colors = sys.argv[index].split(":")
  textColor = (int(colors[0]), int(colors[1]), int(colors[2]))

def getFonts():
  fonts = { }

  for fontDir in fontDirs:
    for path, _, files in os.walk(fontDir):
      for file in files:
        filePath = os.path.join(path, file)
        prefix = file.split(".")[0]
        fonts[prefix] = filePath

  return fonts

askedForArgs = False

fontPath = None
fontSize = None
proposedFont = None
fonts = getFonts()

if sys.argv.__contains__("--font"):
  index = sys.argv.index("--font") + 1
  proposedFont = sys.argv[index].lower()
else:
  askedForArgs = True
  answer = input("Please enter a font to use (type \"list\" to list all available fonts and quit): ").lower()

  if answer == "list":
    for font in fonts.keys():
      print(font)

    exit(0)
  else:
    proposedFont = answer.lower()

for font in fonts.keys():
  if font.lower() == proposedFont:
    fontPath = fonts[font]

if not fontPath:
  print("Invalid font.")
  exit(1)

if sys.argv.__contains__("--font-size"):
  index = sys.argv.index("--font-size") + 1
  fontSize = int(sys.argv[index])
else:
  askedForArgs = True
  userInput = input("Please enter a font size (press ENTER for default): ")
  fontSize = 100 if userInput == "" else int(userInput)

if not fontSize:
  print("Invalid font size.")
  exit(2)

imageFont = ImageFont.truetype(fontPath, fontSize)

averageCharacterWidth = sum(imageFont.getlength(char) for char in ascii_letters) / len(ascii_letters)

phrases = None

if sys.argv.__contains__("--phrases"):
  index = sys.argv.index("--phrases") + 1
  phrases = sys.argv[index:]
else:
  askedForArgs = True
  phrases = input("Please enter the phrases to use (\"^\" separated): ").split("^")

if not phrases or len(phrases) == 0:
  print("Invalid phrases.")
  exit(3)

if not os.path.isdir(tempDir):
  os.mkdir(tempDir)

computationalStartMessagePrefix = '\n' if askedForArgs else ''

## Args: END

## Computation: START

if not os.path.exists(framesPath):
  print(f"{computationalStartMessagePrefix}Downloading frames from the MacStories CDN...\n")

  frames = urllib.request.urlopen("https://cdn.macstories.net/Frames.json")
  with open(framesPath, "w", encoding="utf-8") as output:
    output.write(frames.read().decode("utf-8"))
else: 
  print(f"{computationalStartMessagePrefix}Using existing frames found in \"{tempDir}\"...\n")

for path, dirs, files in os.walk(inputDir):
  files.sort()

  for filename in files:
    extension = filename.split(".")[1].lower()

    if not (extension == "png" or extension == "jpeg" or extension == "jpg" or extension == "tiff"):
      continue

    filepath = os.path.join(path, filename)
    prefix = filename.split("-")[0]

    keys = frameDimensionsLookupTable.keys()

    if prefix not in keys:
      image = Image.open(filepath)
      size = (image.width, image.height)

      for key in keys:
        dimensions = frameDimensionsLookupTable[key]
        
        if dimensions[0] == size[0] and dimensions[1] == size[1]:
          if key in screenshots.keys():
            screenshots.setdefault(key, []).append(filepath)
          else:
            screenshots[key] = [filepath]

          break

    print("Found:", filepath)
    
    if prefix in screenshots.keys():
      screenshots.setdefault(prefix, []).append(filepath)
    else:
      screenshots[prefix] = [filepath]

print("")

if len(screenshots.keys()) == 0:
  print("No files were provided to composite.")
  exit(4)

if not os.path.exists(outputDir):
  os.mkdir(outputDir)

with open(framesPath, "r", encoding="utf-8") as frames:
  data = json.loads(frames.read())

  for prefix in screenshots.keys():
    if prefix in frameDataLookupTable.keys():
      evalBase = "data"

      for subKey in frameDataLookupTable[prefix]:
        evalBase = evalBase.__add__(f"[\"{subKey}\"]")

      frameXOffset = int(eval(evalBase.__add__("[\"x\"]")))
      frameYOffset = int(eval(evalBase.__add__("[\"y\"]")))
      frame = eval(evalBase.__add__("[\"frame\"]"))

      frameData = base64.b64decode(frame)
      frameImage = Image.open(io.BytesIO(frameData))

      outputDimensions = frameDimensionsLookupTable[prefix]
      backgroundImage = Image.new("RGB", outputDimensions, backgroundColor)

      resizeWidth = int(frameImage.width * frameScaleFactor)
      resizeHeight = int(resizeWidth / frameImage.width * frameImage.height)
      resizeDimensions = (resizeWidth, resizeHeight)
      
      x = int((backgroundImage.width - resizeDimensions[0]) / 2)
      y = int(backgroundImage.height * (1 - frameVerticalPaddingFactor) - resizeHeight)

      textX = int(backgroundImage.width * 0.5)
      textY = int(y / 2)

      for index, screenshot in enumerate(screenshots[prefix]):
        compositedImage = Image.new("RGBA", (frameImage.width, frameImage.height), (0, 0, 0, 0))

        screenshotImage = Image.open(screenshot)
        compositedImage.alpha_composite(screenshotImage, dest=(frameXOffset, frameYOffset))

        compositedImage.alpha_composite(frameImage)
        resizedImage = compositedImage.resize(resizeDimensions)
        
        outputImage = backgroundImage.copy()
        outputImage.paste(resizedImage, (x, y), resizedImage)

        outputImageDrawingProxy = ImageDraw.Draw(outputImage)
        tempIndex = index

        while tempIndex + 1 > len(phrases):
          tempIndex -= 1

        text = phrases[tempIndex]
        maximumLineWidth = outputImage.width * maximumLineWidthPercentage / averageCharacterWidth
        wrappedText = textwrap.fill(text=text, width=maximumLineWidth)

        outputImageDrawingProxy.text((textX, textY), wrappedText, fill=textColor, font=imageFont, anchor="mm", spacing=textMultilineSpacing, align=multilineTextAlignment)

        screenshotName = screenshot.removeprefix(inputDir)

        print(f"Finished: {screenshotName}")
        path = os.path.join(outputDir, screenshotName)
        
        if not sys.argv.__contains__("--dry-run"):
          print(f"Saving: {path}")
          outputImage.save(path, "png")
        else:
          print(f"Saving (dry run): {path}")

## Computation: END

exit(0)