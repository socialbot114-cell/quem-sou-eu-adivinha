import Foundation

enum KnowledgeLoadError: Error, Equatable, LocalizedError {
    case missingResource
    case unreadableData
    case decodingFailed

    var errorDescription: String? {
        switch self {
        case .missingResource, .unreadableData:
            return "Não foi possível carregar a base de perguntas."
        case .decodingFailed:
            return "A base de perguntas está corrompida ou incompatível."
        }
    }
}

final class KnowledgeStore {
    static let shared = KnowledgeStore()
    let base: KnowledgeBase
    let loadError: KnowledgeLoadError?
    let fingerprint: String

    private init() {
        do {
            guard let url = Bundle.main.url(forResource: "knowledge", withExtension: "json", subdirectory: "KnowledgeBase") else {
                throw KnowledgeLoadError.missingResource
            }
            guard let data = try? Data(contentsOf: url) else {
                throw KnowledgeLoadError.unreadableData
            }
            let primary = try JSONDecoder().decode(KnowledgeBase.self, from: data)
            if let expansionURL = Bundle.main.url(forResource: "character-expansion", withExtension: "json", subdirectory: "KnowledgeBase") {
                guard let expansionData = try? Data(contentsOf: expansionURL) else {
                    throw KnowledgeLoadError.unreadableData
                }
                let expansion = try JSONDecoder().decode(KnowledgeBase.self, from: expansionData)
                base = KnowledgeBase(
                    people: primary.people + expansion.people,
                    questions: primary.questions + expansion.questions
                )
            } else {
                base = primary
            }
            loadError = nil
        } catch let error as KnowledgeLoadError {
            base = KnowledgeBase(people: [], questions: [])
            loadError = error
        } catch {
            base = KnowledgeBase(people: [], questions: [])
            loadError = .decodingFailed
        }
        fingerprint = KnowledgeStore.computeFingerprint(base)
    }

    private static func computeFingerprint(_ base: KnowledgeBase) -> String {
        let canonical = base.people.map(\.id).sorted().joined(separator: ",")
            + "#" + base.questions.map(\.id).sorted().joined(separator: ",")
        var hash: UInt64 = 1469598103934665603
        for byte in canonical.utf8 {
            hash = (hash ^ UInt64(byte)) &* 1099511628211
        }
        return String(hash, radix: 16)
    }
}
