import Foundation

struct GameEngine {
    let people: [Person]
    let questions: [Question]
    private(set) var scores: [String: Double]
    private(set) var asked: Set<String> = []
    private(set) var askedAttributes: Set<String> = []
    private let chooseCandidateIndex: (Int) -> Int

    init(people: [Person], questions: [Question], randomIndex: @escaping (Int) -> Int = { Int.random(in: 0..<$0) }) {
        self.people = people
        self.questions = questions
        self.chooseCandidateIndex = randomIndex
        self.scores = Dictionary(uniqueKeysWithValues: people.map { ($0.id, 1.0 / Double(max(people.count, 1))) })
    }

    var bestGuess: Person? { people.max { scores[$0.id, default: 0] < scores[$1.id, default: 0] } }
    var confidence: Double { bestGuess.map { scores[$0.id, default: 0] } ?? 0 }

    mutating func nextQuestion() -> Question? {
        guard !people.isEmpty else { return nil }
        let available = questions.filter { !asked.contains($0.id) && !askedAttributes.contains($0.attribute) && informationGain($0) > 0.001 }
        guard !available.isEmpty else { return nil }
        let bestScore = available.map { informationGain($0) }.max() ?? 0
        let candidates = available.filter { informationGain($0) >= bestScore - 0.01 }
        let selectedIndex = chooseCandidateIndex(candidates.count)
        let selected = candidates[selectedIndex]
        asked.insert(selected.id)
        askedAttributes.insert(selected.attribute)
        return selected
    }

    mutating func apply(_ answer: Answer, to question: Question) {
        guard answer != .unknown else { return }
        for person in people {
            let value = person.attributes[question.attribute] ?? 0.5
            scores[person.id] = scores[person.id, default: 0.0] * likelihood(value, answer)
        }
        let total = scores.values.reduce(0, +)
        if total > 0 { for id in scores.keys { scores[id]! /= total } }
    }

    mutating func reject(_ person: Person) {
        scores[person.id] = 0
        let total = scores.values.reduce(0, +)
        guard total > 0 else { return }
        for id in scores.keys { scores[id]! /= total }
    }

    mutating func restore(_ answers: [RecordedAnswer]) {
        for record in answers {
            guard let question = questions.first(where: { $0.id == record.questionID }) else { continue }
            asked.insert(question.id)
            askedAttributes.insert(question.attribute)
            apply(record.answer, to: question)
        }
    }

    private func informationGain(_ question: Question) -> Double {
        let coverage = people.reduce(0.0) { partial, person in
            partial + (person.attributes[question.attribute] == nil ? 0 : scores[person.id, default: 0])
        }
        guard coverage >= 0.6 else { return 0 }

        let priorEntropy = entropy(scores.values)
        let expectedEntropy = Answer.allCases.filter { $0 != .unknown }.reduce(0.0) { total, answer in
            var weighted: [String: Double] = [:]
            for person in people {
                let answerWeight = likelihood(person.attributes[question.attribute] ?? 0.5, answer)
                weighted[person.id] = scores[person.id, default: 0] * answerWeight
            }
            let probability = weighted.values.reduce(0, +)
            guard probability > 0 else { return total }
            return total + probability * entropy(weighted.values.map { $0 / probability })
        }
        return max(0, priorEntropy - expectedEntropy) * coverage
    }

    private func likelihood(_ value: Double, _ answer: Answer) -> Double {
        let raw = max(0.05, 1.0 - abs(value - answer.evidence))
        let total = Answer.allCases
            .filter { $0 != .unknown }
            .reduce(0.0) { $0 + max(0.05, 1.0 - abs(value - $1.evidence)) }
        return raw / total
    }

    private func entropy<S: Sequence>(_ values: S) -> Double where S.Element == Double {
        values.reduce(0.0) { result, value in
            guard value > 0 else { return result }
            return result - value * log2(value)
        }
    }
}
