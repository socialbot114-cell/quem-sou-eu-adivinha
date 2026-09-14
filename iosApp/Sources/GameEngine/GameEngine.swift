import Foundation

struct GameEngine {
    let people: [Person]
    let questions: [Question]
    private(set) var scores: [String: Double]
    private(set) var asked: Set<String> = []

    init(people: [Person], questions: [Question]) {
        self.people = people
        self.questions = questions
        self.scores = Dictionary(uniqueKeysWithValues: people.map { ($0.id, 1.0 / Double(max(people.count, 1))) })
    }

    var bestGuess: Person? { people.max { scores[$0.id, default: 0] < scores[$1.id, default: 0] } }
    var confidence: Double { bestGuess.map { scores[$0.id, default: 0] } ?? 0 }

    mutating func nextQuestion() -> Question? {
        guard !people.isEmpty else { return nil }
        let available = questions.filter { !asked.contains($0.id) }
        guard !available.isEmpty else { return nil }
        let selected = available.max { separation($0) < separation($1) }!
        asked.insert(selected.id)
        return selected
    }

    mutating func apply(_ answer: Answer, to question: Question) {
        for person in people {
            let value = person.attributes[question.attribute, default: 0.5]
            let agreement = 1.0 - abs(value - answer.evidence)
            scores[person.id] = scores[person.id, default: 0.0] * (0.25 + agreement)
        }
        let total = scores.values.reduce(0, +)
        if total > 0 { for id in scores.keys { scores[id]! /= total } }
    }

    private func separation(_ question: Question) -> Double {
        let weighted = people.map { scores[$0.id, default: 0] * $0.attributes[question.attribute, default: 0.5] }
        let yes = weighted.reduce(0, +)
        return 1.0 - abs(0.5 - yes)
    }
}
