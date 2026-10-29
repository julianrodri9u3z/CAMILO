// vision_analyze.swift -- macOS-only (Apple Vision). Per-frame person MATTES + face/hand ZONES for a video.
//   swiftc -O -swift-version 5 -o vision_analyze vision_analyze.swift        (done automatically by vision_analyze.py)
//   ./vision_analyze <video> <out_dir> [--matte-width 540] [--quality accurate|balanced|fast]
//                    [--start S] [--dur D] [--no-matte] [--no-zones] [--zone-step 3] [--no-png]
// Writes:  <out_dir>/matte/m_000001.png  (RGBA: black + alpha = person, one per SOURCE frame, 1-based)
//          <out_dir>/zones.json          ({fps,w,h,frames:[{i,t,faces,hands,person}]}, rects normalized, origin TOP-LEFT)
// Why: "text behind the person" needs the person alpha per frame; "captions that dodge faces/hands" needs boxes.
// Source frame i (1-based) is at time firstT + (i-1)/fps (firstT is in zones.json); the matte folder is addressed by source frame, not output frame.
import Foundation
import AVFoundation
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins

var args = Array(CommandLine.arguments.dropFirst())
func opt(_ name: String, _ def: String) -> String {
    if let i = args.firstIndex(of: name), i + 1 < args.count { return args[i + 1] }
    return def
}
func flag(_ name: String) -> Bool { args.contains(name) }
guard args.count >= 2 else { print("usage: vision_analyze <video> <out_dir> [options]"); exit(2) }
let videoPath = args[0], outDir = args[1]
let outW = Int(opt("--matte-width", "540"))!
let quality = opt("--quality", "accurate")
let startS = Double(opt("--start", "0"))!
let durS = Double(opt("--dur", "0"))!
let zoneStep = Int(opt("--zone-step", "3"))!
let doMatte = !flag("--no-matte"), doZones = !flag("--no-zones"), writePng = !flag("--no-png")

let fm = FileManager.default
let matteDir = outDir + "/matte"
try fm.createDirectory(atPath: matteDir, withIntermediateDirectories: true)

let asset = AVURLAsset(url: URL(fileURLWithPath: videoPath))
let tracks = try await asset.loadTracks(withMediaType: .video)
guard let track = tracks.first else { print("no video track"); exit(1) }
let size = try await track.load(.naturalSize)
let fps = Double(try await track.load(.nominalFrameRate))
let reader = try AVAssetReader(asset: asset)
if durS > 0 || startS > 0 {
    let total = try await asset.load(.duration).seconds
    reader.timeRange = CMTimeRange(start: CMTime(seconds: startS, preferredTimescale: 600),
                                   duration: CMTime(seconds: durS > 0 ? durS : total - startS, preferredTimescale: 600))
}
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(output)
reader.startReading()

let seg = VNGeneratePersonSegmentationRequest()
seg.qualityLevel = quality == "fast" ? .fast : (quality == "balanced" ? .balanced : .accurate)
seg.outputPixelFormat = kCVPixelFormatType_OneComponent8
let faceReq = VNDetectFaceRectanglesRequest()
let handReq = VNDetectHumanHandPoseRequest()
handReq.maximumHandCount = 2
let seqHandler = VNSequenceRequestHandler()          // stateful: keeps temporal smoothing between frames
let ci = CIContext()
let srgb = CGColorSpace(name: CGColorSpace.sRGB)!
let outH = Int((Double(outW) * Double(size.height) / Double(size.width)).rounded())

func topLeft(_ r: CGRect) -> [Double] { [Double(r.minX), Double(1 - r.maxY), Double(r.width), Double(r.height)] }
func personBox(_ pb: CVPixelBuffer) -> [Double]? {
    CVPixelBufferLockBaseAddress(pb, .readOnly); defer { CVPixelBufferUnlockBaseAddress(pb, .readOnly) }
    let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb), bpr = CVPixelBufferGetBytesPerRow(pb)
    guard let base = CVPixelBufferGetBaseAddress(pb)?.assumingMemoryBound(to: UInt8.self) else { return nil }
    var x0 = w, x1 = -1, y0 = h, y1 = -1
    var y = 0
    while y < h {
        var x = 0
        while x < w {
            if base[y * bpr + x] > 127 { if x < x0 { x0 = x }; if x > x1 { x1 = x }; if y < y0 { y0 = y }; if y > y1 { y1 = y } }
            x += 4
        }
        y += 4
    }
    if x1 < 0 { return nil }
    return [Double(x0) / Double(w), Double(y0) / Double(h), Double(x1 - x0) / Double(w), Double(y1 - y0) / Double(h)]
}

var frames: [[String: Any]] = []
var idx = 0
var firstT = 0.0
let t0 = Date()
while let sb = output.copyNextSampleBuffer() {
    guard let pb = CMSampleBufferGetImageBuffer(sb) else { continue }
    idx += 1
    let t = CMSampleBufferGetPresentationTimeStamp(sb).seconds
    if idx == 1 { firstT = t }
    var reqs: [VNRequest] = []
    if doMatte { reqs.append(seg) }
    let doZoneNow = doZones && (idx % zoneStep == 1 || zoneStep <= 1)
    if doZoneNow { reqs += [faceReq, handReq] }
    try seqHandler.perform(reqs, on: pb, orientation: .up)

    var person: [Double]? = nil
    if doMatte, let obs = seg.results?.first {
        let mpb = obs.pixelBuffer
        person = personBox(mpb)
        if writePng {
        let m = CIImage(cvPixelBuffer: mpb)
        let scaled = m.transformed(by: CGAffineTransform(scaleX: CGFloat(outW) / m.extent.width, y: CGFloat(outH) / m.extent.height))
        let black = CIImage(color: CIColor.black).cropped(to: scaled.extent)
        let clear = CIImage(color: CIColor.clear).cropped(to: scaled.extent)
        let f = CIFilter.blendWithMask()
        f.inputImage = black; f.backgroundImage = clear; f.maskImage = scaled
        let name = String(format: "%@/m_%06d.png", matteDir, idx)
        try ci.writePNGRepresentation(of: f.outputImage!, to: URL(fileURLWithPath: name), format: .RGBA8, colorSpace: srgb)
        }
    }
    if doZoneNow {
        var faces: [[Double]] = [], hands: [[Double]] = []
        for r in (faceReq.results ?? []) { faces.append(topLeft(r.boundingBox)) }
        for h in (handReq.results ?? []) {
            guard let pts = try? h.recognizedPoints(.all) else { continue }
            let good = pts.values.filter { $0.confidence > 0.3 }
            if good.count < 5 { continue }
            let xs = good.map { $0.location.x }, ys = good.map { $0.location.y }
            let r = CGRect(x: xs.min()!, y: ys.min()!, width: xs.max()! - xs.min()!, height: ys.max()! - ys.min()!).insetBy(dx: -0.03, dy: -0.03)
            hands.append(topLeft(r))
        }
        frames.append(["i": idx, "t": (t * 1000).rounded() / 1000, "faces": faces, "hands": hands, "person": person as Any])
    } else if doMatte {
        // keep the person box for every frame so top-of-head can be tracked smoothly
    }
    if idx % 120 == 0 { FileHandle.standardError.write("frame \(idx) (\(Int(Date().timeIntervalSince(t0)))s)\n".data(using: .utf8)!) }
}
let doc: [String: Any] = ["fps": fps, "w": Int(size.width), "h": Int(size.height), "matteW": outW, "matteH": outH, "frameCount": idx, "start": startS, "firstT": firstT, "frames": frames]
let data = try JSONSerialization.data(withJSONObject: doc, options: [.prettyPrinted])
try data.write(to: URL(fileURLWithPath: outDir + "/zones.json"))
print("done: \(idx) frames in \(Int(Date().timeIntervalSince(t0)))s -> \(outDir)")
