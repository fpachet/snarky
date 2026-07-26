#!/usr/bin/env swift

import Foundation
import ImageIO
import Vision

struct OCRLine: Codable {
    let text: String
    let confidence: Float
    let bbox: [Double]
}

guard CommandLine.arguments.count == 3 else {
    fputs("usage: vision_ocr.swift INPUT_IMAGE OUTPUT_JSON\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])

guard
    let source = CGImageSourceCreateWithURL(inputURL as CFURL, nil),
    let image = CGImageSourceCreateImageAtIndex(source, 0, nil)
else {
    fputs("cannot load image: \(inputURL.path)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en-US"]
request.usesLanguageCorrection = true
request.minimumTextHeight = 0.006

let handler = VNImageRequestHandler(cgImage: image, options: [:])
try handler.perform([request])

let observations = (request.results ?? []).sorted {
    let y0 = $0.boundingBox.maxY
    let y1 = $1.boundingBox.maxY
    if abs(y0 - y1) > 0.004 {
        return y0 > y1
    }
    return $0.boundingBox.minX < $1.boundingBox.minX
}

let lines: [OCRLine] = observations.compactMap { observation in
    guard let candidate = observation.topCandidates(1).first else {
        return nil
    }
    let box = observation.boundingBox
    return OCRLine(
        text: candidate.string,
        confidence: candidate.confidence,
        bbox: [box.minX, box.minY, box.maxX, box.maxY]
    )
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let data = try encoder.encode(lines)
try data.write(to: outputURL, options: .atomic)
