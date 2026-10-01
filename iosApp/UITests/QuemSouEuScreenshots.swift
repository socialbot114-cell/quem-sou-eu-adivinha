import XCTest

final class QuemSouEuScreenshots: XCTestCase {
    func testRoundCanWinAfterOneContradictoryAnswerInUI() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        let categoriesTab = app.buttons["tab.categories"]
        XCTAssertTrue(categoriesTab.waitForExistence(timeout: 8))
        categoriesTab.tap()

        let categoryScroll = app.scrollViews.firstMatch
        let artists = app.buttons["category.Artistas brasileiros"]
        XCTAssertTrue(categoryScroll.waitForExistence(timeout: 4))
        for _ in 0..<4 where !artists.isHittable {
            categoryScroll.swipeDown()
        }
        XCTAssertTrue(artists.isHittable)
        artists.tap()

        let targetAnswers = [
            "brazilian": "Sim",
            "alive": "Não",
            "male": "Não",
            "born_before_1970": "Não",
            "born_before_1990": "Não",
            "born_before_1975": "Não",
            "football": "Não",
            "artist": "Sim",
            "creator": "Não",
            "politician": "Não",
            "historical": "Sim",
            "singer": "Sim",
            "actor": "Não",
            "presenter": "Não",
            "writer": "Não",
            "instrumentalist": "Sim",
            "director": "Não",
            "grammy_winner": "Não",
            "samba_artist": "Não",
            "sertanejo_artist": "Sim",
        ]

        var contradictedFirstAnswer = false
        var foundTarget = false
        for _ in 0..<20 {
            let confirm = app.buttons["Acertou!"]
            if confirm.waitForExistence(timeout: 1.5) {
                if app.staticTexts["Marília Mendonça"].exists {
                    confirm.tap()
                    foundTarget = app.staticTexts["ACERTEI!"].waitForExistence(timeout: 6)
                    break
                }
                let reject = app.buttons["Não foi dessa vez"]
                if reject.exists {
                    reject.tap()
                    continue
                }
                break
            }
            if app.staticTexts["Quase!"].exists { break }

            let activeAttribute = targetAnswers.keys.first { app.staticTexts["question.\($0)"].exists }
            guard let activeAttribute, let truth = targetAnswers[activeAttribute] else {
                XCTFail("A rodada apresentou uma pergunta sem resposta-alvo mapeada")
                break
            }
            var answer = truth
            if !contradictedFirstAnswer {
                answer = truth == "Sim" ? "Não" : "Sim"
                contradictedFirstAnswer = true
            }
            let answerButton = app.buttons[answer].firstMatch
            XCTAssertTrue(answerButton.waitForExistence(timeout: 4))
            answerButton.tap()
        }

        XCTAssertTrue(contradictedFirstAnswer)
        XCTAssertTrue(foundTarget, "A rodada não terminou em vitória após uma resposta contraditória")
    }

    func testUndoLastAnswerReturnsToTheSameQuestion() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        let categoriesTab = app.buttons["tab.categories"]
        XCTAssertTrue(categoriesTab.waitForExistence(timeout: 8))
        categoriesTab.tap()

        let categoryScroll = app.scrollViews.firstMatch
        let artists = app.buttons["category.Artistas brasileiros"]
        XCTAssertTrue(categoryScroll.waitForExistence(timeout: 4))
        for _ in 0..<4 where !artists.isHittable {
            categoryScroll.swipeDown()
        }
        XCTAssertTrue(artists.isHittable)
        artists.tap()

        XCTAssertTrue(app.buttons["Sim"].waitForExistence(timeout: 8))
        let firstQuestion = app.staticTexts.matching(NSPredicate(format: "identifier BEGINSWITH 'question.'")).firstMatch
        XCTAssertTrue(firstQuestion.waitForExistence(timeout: 4))
        let firstIdentifier = firstQuestion.identifier
        let undo = app.buttons["game.undo"]
        XCTAssertFalse(undo.exists, "Não deve haver o que desfazer antes da primeira resposta")

        app.buttons["Sim"].firstMatch.tap()
        XCTAssertTrue(undo.waitForExistence(timeout: 4))
        undo.tap()

        XCTAssertTrue(app.staticTexts[firstIdentifier].waitForExistence(timeout: 4), "Desfazer deve mostrar a mesma pergunta")
        XCTAssertFalse(undo.exists, "Depois de desfazer a única resposta não deve sobrar o que desfazer")
    }

    func testCaptureStoreScreens() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        if app.buttons["Pular"].waitForExistence(timeout: 2) {
            app.buttons["Pular"].tap()
        }

        XCTAssertTrue(app.buttons["home.play"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-home")

        let categoriesTab = app.buttons["tab.categories"]
        XCTAssertTrue(categoriesTab.waitForExistence(timeout: 8))
        categoriesTab.tap()
        XCTAssertTrue(app.buttons["category.all"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-categorias-inicio")

        let categoryScroll = app.scrollViews.firstMatch
        XCTAssertTrue(categoryScroll.waitForExistence(timeout: 4))
        categoryScroll.swipeUp()
        let internationalMusic = app.buttons["category.Música internacional"]
        XCTAssertTrue(internationalMusic.waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-categorias-expansao")
        let artists = app.buttons["category.Artistas brasileiros"]
        for _ in 0..<4 where !artists.isHittable {
            categoryScroll.swipeDown()
        }
        XCTAssertTrue(artists.isHittable)
        artists.tap()
        XCTAssertTrue(app.buttons["Sim"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-jogo-artistas-brasileiros")

        let targetAnswers = [
            "brazilian": "Sim",
            "alive": "Sim",
            "male": "Não",
            "born_before_1970": "Não",
            "born_before_1990": "Não",
            "born_before_1975": "Não",
            "football": "Não",
            "artist": "Sim",
            "creator": "Não",
            "politician": "Não",
            "historical": "Não",
            "singer": "Sim",
            "actor": "Sim",
            "presenter": "Sim",
            "writer": "Não",
            "instrumentalist": "Não",
            "director": "Não",
            "grammy_winner": "Não",
            "samba_artist": "Não",
            "sertanejo_artist": "Não",
        ]

        for _ in 0..<14 {
            if app.staticTexts["Já tenho um palpite!"].exists { break }
            let activeAttribute = targetAnswers.keys.first { app.staticTexts["question.\($0)"].exists }
            guard let activeAttribute, let answer = targetAnswers[activeAttribute] else {
                XCTFail("Nenhuma pergunta mapeada para o personagem de screenshot apareceu")
                break
            }
            let answerButton = app.buttons[answer].firstMatch
            XCTAssertTrue(answerButton.waitForExistence(timeout: 4))
            answerButton.tap()
        }
        XCTAssertTrue(app.staticTexts["Já tenho um palpite!"].waitForExistence(timeout: 12))
        XCTAssertTrue(app.staticTexts["Anitta"].waitForExistence(timeout: 4))
        capture(app, name: "quem-sou-eu-palpite-anitta")
        let confirm = app.buttons["Acertou!"]
        XCTAssertTrue(confirm.waitForExistence(timeout: 4))
        confirm.tap()
        XCTAssertTrue(app.staticTexts["ACERTEI!"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-resultado-vitoria")

        let changeCategory = app.buttons["Escolher outra categoria"]
        XCTAssertTrue(changeCategory.waitForExistence(timeout: 5))
        changeCategory.tap()

        let kpopScroll = app.scrollViews.firstMatch
        XCTAssertTrue(kpopScroll.waitForExistence(timeout: 4))
        let kpop = app.buttons["category.K-pop"]
        for _ in 0..<5 where !kpop.isHittable {
            kpopScroll.swipeUp()
        }
        XCTAssertTrue(kpop.isHittable)
        kpop.tap()
        XCTAssertTrue(app.buttons["Sim"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-jogo-kpop")

        let kpopTargetAnswers = [
            "brazilian": "Não",
            "alive": "Sim",
            "male": "Sim",
            "born_before_1970": "Não",
            "born_before_1990": "Sim",
            "football": "Não",
            "artist": "Sim",
            "creator": "Não",
            "politician": "Não",
            "historical": "Não",
            "bts_member": "Não",
            "blackpink_member": "Não",
            "solo_artist": "Sim",
            "rapper": "Sim",
            "born_before_1994": "Sim",
            "born_before_1993": "Sim",
            "born_in_south_korea": "Sim",
            "known_for_dance": "Sim",
            "kpop_born_before_1996": "Sim",
            "born_before_1995": "Sim",
            "born_before_1998": "Sim",
            "born_before_1980": "Sim",
            "born_before_2000": "Sim",
            "stray_kids_member": "Não",
            "twice_member": "Não",
            "exo_member": "Não",
            "shinee_member": "Não",
            "gidle_member": "Não",
            "aespa_member": "Não",
            "ive_member": "Não",
            "bigbang_member": "Não",
            "ioi_member": "Não",
        ]

        for _ in 0..<14 {
            if app.staticTexts["Já tenho um palpite!"].exists { break }
            let activeAttribute = kpopTargetAnswers.keys.first { app.staticTexts["question.\($0)"].exists }
            guard let activeAttribute, let answer = kpopTargetAnswers[activeAttribute] else {
                XCTFail("Nenhuma pergunta mapeada para PSY apareceu")
                break
            }
            let answerButton = app.buttons[answer].firstMatch
            XCTAssertTrue(answerButton.waitForExistence(timeout: 4))
            answerButton.tap()
        }
        XCTAssertTrue(app.staticTexts["Já tenho um palpite!"].waitForExistence(timeout: 12))
        XCTAssertTrue(app.staticTexts["PSY"].waitForExistence(timeout: 4))
        capture(app, name: "quem-sou-eu-palpite-psy")
        let kpopConfirm = app.buttons["Acertou!"]
        XCTAssertTrue(kpopConfirm.waitForExistence(timeout: 4))
        kpopConfirm.tap()
        XCTAssertTrue(app.staticTexts["ACERTEI!"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-resultado-vitoria-psy")

        let returnToCategories = app.buttons["Escolher outra categoria"]
        XCTAssertTrue(returnToCategories.waitForExistence(timeout: 5))
        returnToCategories.tap()
        let profileTab = app.buttons["tab.profile"]
        XCTAssertTrue(profileTab.waitForExistence(timeout: 5))
        profileTab.tap()
        XCTAssertTrue(app.staticTexts["Perfil e ajustes"].waitForExistence(timeout: 5))
        capture(app, name: "quem-sou-eu-perfil")
    }

    private func capture(_ app: XCUIApplication, name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
