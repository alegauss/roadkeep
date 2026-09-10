// Render build/icon.svg to build/icon.png, which is what electron-builder makes every icon
// from — the Windows .ico, the macOS .icns and the Linux PNGs (RG138).
//
// With the Electron this repository already has, rather than a rasteriser added to the
// toolchain for one file: Chromium draws the SVG, offscreen, and the capture is the icon.
//
//   npm run icon
//
// Run it after editing icon.svg; the PNG is committed beside it. Two things it has to force:
// a device scale of 1, or a high-density screen hands back a capture twice the size asked
// for; and a transparent window, or the tile's rounded corners come out filled.
//
// `ELECTRON_RUN_AS_NODE` from an editor terminal makes this plain Node, where `electron` is
// a path and not a module — the same trap `electron-builder.yml` notes for the packaged app.
const path = require('node:path')
const fs = require('node:fs')

const electron = require('electron')
if (typeof electron === 'string') {
  console.error('render-icon: ELECTRON_RUN_AS_NODE is set, so this is running as Node. Unset it.')
  process.exit(1)
}
const { app, BrowserWindow } = electron

const SIZE = 1024
const SOURCE = path.join(__dirname, 'icon.svg')
const TARGET = path.join(__dirname, 'icon.png')

app.commandLine.appendSwitch('force-device-scale-factor', '1')

void app.whenReady().then(async () => {
  const win = new BrowserWindow({
    width: SIZE,
    height: SIZE,
    useContentSize: true,
    show: false,
    transparent: true,
    frame: false,
    backgroundColor: '#00000000',
    webPreferences: { offscreen: true },
  })
  const svg = fs.readFileSync(SOURCE, 'utf8')
  const page = `<!doctype html><html><head><style>html,body{margin:0;background:transparent}svg{display:block}</style></head><body>${svg}</body></html>`
  await win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(page)}`)
  await new Promise((done) => setTimeout(done, 500))

  const image = await win.webContents.capturePage({ x: 0, y: 0, width: SIZE, height: SIZE })
  const { width, height } = image.getSize()
  if (width !== SIZE || height !== SIZE) {
    console.error(`render-icon: captured ${width}x${height}, expected ${SIZE}x${SIZE}`)
    app.exit(1)
    return
  }
  fs.writeFileSync(TARGET, image.toPNG())
  console.log(`render-icon: wrote ${path.relative(process.cwd(), TARGET)} at ${width}x${height}`)
  app.quit()
})
