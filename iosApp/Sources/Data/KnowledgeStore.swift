import Foundation

final class KnowledgeStore {
    static let shared = KnowledgeStore()
    let base: KnowledgeBase
    let loadError: String?

    private init() {
        guard let url = Bundle.main.url(forResource: "knowledge", withExtension: "json", subdirectory: "KnowledgeBase"),
              let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode(KnowledgeBase.self, from: data) else {
            base = KnowledgeBase(people: [], questions: [])
            loadError = "Não foi possível carregar a base de perguntas."
            return
        }
        base = decoded
        loadError = nil
    }
}
