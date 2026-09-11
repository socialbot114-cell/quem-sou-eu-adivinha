import Foundation

enum Category: String, Codable, CaseIterable, Identifiable {
    case tiktok = "TikTok"
    case instagram = "Instagram"
    case football = "Futebol"
    case artists = "Artistas brasileiros"
    case politicians = "Políticos"
    case history = "História"
    case world = "Personalidades mundiais"
    case all = "Todos"
    var id: String { rawValue }
    var symbol: String {
        switch self { case .tiktok: "play.rectangle.fill"; case .instagram: "camera.fill"; case .football: "soccerball"; case .artists: "music.note"; case .politicians: "building.columns.fill"; case .history: "clock.fill"; case .world: "globe.americas.fill"; case .all: "sparkles" }
    }
}

enum Answer: String, CaseIterable, Identifiable {
    case yes = "Sim"
    case probablyYes = "Provavelmente sim"
    case unknown = "Não sei"
    case probablyNo = "Provavelmente não"
    case no = "Não"
    var id: String { rawValue }
    var evidence: Double { switch self { case .yes: 1; case .probablyYes: 0.75; case .unknown: 0.5; case .probablyNo: 0.25; case .no: 0 } }
}

struct Person: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let categories: [Category]
    let country: String
    let profession: String
    let attributes: [String: Double]
    let avatarSymbol: String
}

struct Question: Codable, Identifiable, Equatable {
    let id: String
    let text: String
    let attribute: String
    let categories: [Category]
}

struct KnowledgeBase: Codable {
    let people: [Person]
    let questions: [Question]
}
