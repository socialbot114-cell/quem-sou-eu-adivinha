import Foundation

final class KnowledgeStore {
    static let shared = KnowledgeStore()
    let base: KnowledgeBase

    private init() {
        guard let url = Bundle.main.url(forResource: "knowledge", withExtension: "json", subdirectory: "KnowledgeBase"),
              let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode(KnowledgeBase.self, from: data) else {
            base = KnowledgeBase(people: [], questions: [])
            return
        }
        base = decoded
    }
}
