import XCTest

final class QuemSouEuScreenshots: XCTestCase {
    func testCaptureStoreScreens() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        if app.buttons["Pular"].waitForExistence(timeout: 3) {
            app.buttons["Pular"].tap()
        }

        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "quem-sou-eu-home"
        screenshot.lifetime = .keepAlways
        add(screenshot)

        if app.buttons["Jogar"].waitForExistence(timeout: 3) {
            app.buttons["Jogar"].tap()
            let categories = XCTAttachment(screenshot: app.screenshot())
            categories.name = "quem-sou-eu-categorias"
            categories.lifetime = .keepAlways
            add(categories)
        }
    }
}
