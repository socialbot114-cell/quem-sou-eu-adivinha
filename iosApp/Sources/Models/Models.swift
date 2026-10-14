import Foundation

enum Category: String, Codable, CaseIterable, Identifiable {
    case creators = "Criadores digitais"
    case football = "Futebol"
    case artists = "Artistas brasileiros"
    case politicians = "Políticos"
    case history = "História"
    case world = "Personalidades mundiais"
    case otherSports = "Outros esportes"
    case internationalMusic = "Música internacional"
    case kpop = "K-pop"
    case cinema = "Cinema e TV"
    case fashion = "Moda e reality"
    case technology = "Tecnologia e negócios"
    case all = "Todos"
    var id: String { rawValue }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let value = try container.decode(String.self)
        if value == "TikTok" || value == "Instagram" {
            self = .creators
        } else if let category = Category(rawValue: value) {
            self = category
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Categoria desconhecida: \(value)")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(rawValue)
    }

    var symbol: String {
        switch self {
        case .creators: "play.rectangle.fill"
        case .football: "soccerball"
        case .artists, .internationalMusic, .kpop: "music.note"
        case .politicians: "building.columns.fill"
        case .history: "clock.fill"
        case .world: "globe.americas.fill"
        case .otherSports: "sportscourt.fill"
        case .cinema: "film.fill"
        case .fashion: "tshirt.fill"
        case .technology: "lightbulb.fill"
        case .all: "sparkles"
        }
    }
}

enum Answer: String, Codable, CaseIterable, Identifiable {
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
    let imageName: String?

    init(id: String, name: String, categories: [Category], country: String, profession: String, attributes: [String: Double], avatarSymbol: String, imageName: String? = nil) {
        self.id = id
        self.name = name
        self.categories = categories
        self.country = country
        self.profession = profession
        self.attributes = attributes
        self.avatarSymbol = avatarSymbol
        self.imageName = imageName
    }
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
