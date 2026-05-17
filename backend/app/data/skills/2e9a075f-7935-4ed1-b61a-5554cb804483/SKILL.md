---
name: code-backend-java-spring
description: Java と Spring Boot のバックエンドコードの生成・レビューに使用。レイヤーアーキテクチャ、DTOバリデーション、MyBatis SQL、セキュリティ、Spring Bootベストプラクティス、命名規則、コメント、例外処理に従う。コード生成時は要件・設計を参照し本スキルの references に沿って実装する。レビュー時は references をチェックリストとして適用し指摘・修正案を出力する。backend 配下の .java / .xml の生成・レビュー要求時に使用。
---

# バックエンド Java & Spring Boot コード生成・レビュー

Java と Spring Boot のバックエンドコードに対して、**コード生成**または**コードレビュー**のいずれかに本スキルを使用する。プロジェクト固有のコーディング規約とベストプラクティスは、本スキル内の references に従う。

## 使用タイミング

- **コード生成**: Controller / Service / Mapper / DTO / Entity の新規作成・追記、API 追加、機能追加
- **コードレビュー**: Java クラス（Controller、Service、Mapper、DTO、Entity）のレビュー、MyBatis XML マッパーファイルのレビュー、Spring Boot 設定ファイルのレビュー、バックエンドコードの git 変更分析、コミット前のコードレビュー、リファクタリングの検証

---

## タスク別の実施手順

利用目的に応じて、次のいずれかの手順を実施する。

---

### タスク A: コードの生成（新規・追記・更新）

**いつ使う**: 要件や設計書に基づいてバックエンドコードを新規作成する、または既存コードに追記・更新するとき。

| 手順 | 実施内容 |
|------|----------|
| A-1 | **対象の確定** - 生成・更新する対象を特定する（例：会議更新 API の追加、TODO 一覧取得の Service 追加、新規 Entity）。 |
| A-2 | **入力の確認** - 要件書・設計書（API 定義書・テーブル定義・ビジネスルール）を確認し、仕様・制約を把握する。 |
| A-3 | **参照の読み込み** - 対象レイヤー・ファイル種別に応じて、下記「レビューチェックリスト」各観点の参照ファイルを読み、命名・レイヤー・バリデーション・SQL・セキュリティ・ログ・例外のルールを把握する。 |
| A-4 | **実装** - references に沿ってコードを執筆する。Controller は HTTP のみ、Service にビジネスロジック、Mapper は DB アクセスのみ。DTO は Request/Response のバリデーション、例外は Handler に委ねる。Java クラスを生成・更新する場合は `references/comment-checklist.md` を実装時点から適用し、クラスコメント・フィールド説明・public メソッド Javadoc（`@param` / `@return` / `@throws`）を付与する。 |
| A-5 | **自己チェック** - 生成・更新した範囲について、下記「レビューチェックリスト」のクイックチェックを適用し、重大な規約違反がないか確認する。特に `references/comment-checklist.md` は必須ゲートとし、未達項目が1つでもある場合は完了扱いにしない。必要なら修正する。 |

- 複数レイヤーを同時に追加する場合は、Controller → Service → Mapper（＋ DTO / Entity）の順で参照を確認しながら実装する。

---

### タスク B: コードのレビュー

**いつ使う**: 既存のバックエンドコードが規約・ベストプラクティスに沿っているか確認し、指摘や修正案を出したいとき。

| 手順 | 実施内容 |
|------|----------|
| B-1 | **対象の確定** - レビューするファイルまたは git 変更範囲を特定する。 |
| B-2 | **初期分析** - 対象を読み、以下を理解する：クラスの役割と責務（Controller/Service/Mapper/DTO/Entity）、レイヤー間の依存関係、データフローとビジネスロジック、セキュリティ上の考慮事項。 |
| B-3 | **参照の読み込み** - 対象ファイル種別に応じて、下記「レビューチェックリスト」各観点の参照ファイルを読み、チェック観点を把握する。 |
| B-4 | **チェックリストの適用** - 下記「レビューチェックリスト」を順に適用し、命名・レイヤー・DTO・MyBatis・セキュリティ・ログ・スレッドセーフティ・コメント・例外について不整合・規約違反を洗い出す。 |
| B-5 | **レビューレポートの出力** - 重要度別（重大・警告・提案）に指摘をまとめ、ファイル:行参照と修正推奨事項を出力する。良い点も記載する。 |

- レビューレポートの形式は、下記「レビューレポートの形式」に従う。

---

## レビューチェックリスト（タスク A の自己チェック・タスク B の適用）

以下のカテゴリを順番にチェックする。各観点の詳細は、その下に記載した参照ファイルを参照。

#### 命名規約
詳細は [references/naming-conventions.md](references/naming-conventions.md) を参照。

クイックチェック：
- パッケージ：小文字（`controller`、`service`、`dto`、`entity`、`mapper`）
- クラス：PascalCase（`TodoController`、`TodoService`、`TodoMapper`）
- メソッド・変数：camelCase（`getTodo`、`createTodo`）
- 定数：UPPER_SNAKE_CASE（`MAX_RETRY_COUNT`）
- DTO：`XxxRequest`、`XxxResponse`、`XxxCandidate` / Entity：`XxxEntity`
- API パス：`/api/リソース複数形`（`/api/meetings`、`/api/todos`）

#### レイヤーアーキテクチャ
詳細は [references/layer-architecture.md](references/layer-architecture.md) を参照。

クイックチェック：
- Controller：HTTP 処理のみ、ビジネスロジック禁止
- Service：ビジネスロジック、トランザクション管理
- Mapper：データベースアクセスのみ
- データアクセスは MyBatis Mapper（`*Mapper.java` / `*Mapper.xml`）に一元化し、Controller / Service / Security / Config で `JdbcTemplate` / `NamedParameterJdbcTemplate` を注入・利用しない
- 依存方向：Controller → Service → Mapper

#### DTOバリデーション
詳細は [references/dto-validation.md](references/dto-validation.md) を参照。

クイックチェック：
- リクエスト DTO に `@NotBlank`、`@NotNull`、`@Pattern` 等
- DTO にデフォルト値を設定しない（Service 層で設定）
- バリデーションメッセージは多言語対応（messages.properties）
- レスポンス DTO にエラーフィールドを含める

#### MyBatis SQL
詳細は [references/mybatis-sql.md](references/mybatis-sql.md) を参照。

クイックチェック：
- `SELECT *` 禁止、カラムを明示
- SQL は読みやすくフォーマット、パラメータバインディング（`#{param}`）
- ResultMap を明示、インデックスを考慮した WHERE 句

#### セキュリティ
詳細は [references/security.md](references/security.md) を参照。

クイックチェック：
- API Key / 認証は Service 層で検証
- 権限判定は `@PreAuthorize` / `@Secured` / `@RolesAllowed` を優先し、手書き if 判定を分散させない
- 手動権限判定が必要な例外ケースは `AuthorizationService` / `PermissionEvaluator` に集約
- CORS は明示指定（ワイルドカード禁止）
- 機密情報は環境変数、SQL はパラメータバインディング、機密情報のログ禁止

#### Spring Boot ベストプラクティス
詳細は [references/spring-boot-best-practices.md](references/spring-boot-best-practices.md) を参照。

クイックチェック：
- コンストラクタインジェクション（`@RequiredArgsConstructor`）
- 例外は `@ControllerAdvice` で一元、トランザクションは `@Transactional`
- REST の HTTP メソッド・ステータスコード準拠

#### ログ追跡（traceId）・ログ番号
詳細は [references/logging.md](references/logging.md) を参照。

クイックチェック：
- **traceId**: 1 リクエスト 1 つの一意 ID（形式: **時刻(ミリ秒 yyyyMMddHHmmssSSS) + 4 桁 hex**）、Filter + MDC、ログパターンに `%X{traceId}`、リクエスト終了時に MDC.remove
- **ログ番号**: **LogHelper** にログ番号（12 文字: レベル 1 + 業務 ID 3 + 機能 ID 4 + 連番 4）と引数を渡して出力。文言は messages.properties のキーで定義し直書きしない。Controller/Service では log を渡さず `logHelper.info("番号", args)` を使用（@Slf4j 不要）
- **メソッドログは AOP で共通化**: Controller/Service の public メソッドの入退場ログは各メソッド内で書かず、Spring AOP（例: LoggingAspect）で一括出力する
- **例外ログは GlobalExceptionHandler に集約**: スローする例外のログは Handler でのみ出す。業務コードでは「log してから throw」しない。再スローしない例外（例: SSE 内で握りつぶす場合）のみその場でログする
- **例外のログ番号は業務コードから渡す**: BusinessException 系はスロー時に logCode を渡し、Handler では `ex.getLogCode()` を優先して使用する。Handler 側で固定のログ番号にしない（発生箇所の特定のため）

#### スレッドセーフティ
詳細は [references/thread-safety.md](references/thread-safety.md) を参照。

クイックチェック：
- Singleton Bean に可変のインスタンス変数（List・Map・setter で変更するフィールド）がないか
- 必要ならリクエストスコープ・ThreadLocal・スレッドセーフなコレクションを検討

#### コードコメント
詳細は [references/comment-checklist.md](references/comment-checklist.md) を参照。

クイックチェック：
- クラスに目的・概要、フィールドに説明、public メソッドに Javadoc（`@param`、`@return`、`@throws`）
- 複雑なロジックに理由または要約

必須ルール（生成タスク時）：
- Java クラス（Controller / Service / DTO / Entity / Config など）を新規作成・更新した場合、上記クイックチェックをすべて満たすこと
- selfcheck で不足を検出した場合は修正完了まで繰り返し、未修正のまま完了報告しないこと

#### 例外処理
詳細は [references/exception-handling.md](references/exception-handling.md) を参照。

クイックチェック：
- Controller 層では例外を catch しない
- ユーザー向けメッセージは messages.properties、エラーレスポンスは API 仕様準拠
- 適切な例外タイプ（`ResourceNotFoundException`、`ExternalApiException` 等）

---

## レビューレポートの形式（タスク B 用）

以下の形式で結果を提供する。

```
## コードレビューサマリー

### 重大な問題（必須修正）
- [ファイル:行] 問題の説明と修正推奨事項

### 警告（修正推奨）
- [ファイル:行] 問題の説明と改善提案

### 提案（改善案）
- [ファイル:行] 最適化または機能強化のアイデア

### 良い点
- 適切に実装されたパターンや良い実践例
```

### 重要度レベル

**重大**：機能を破壊する、セキュリティ問題、コア規約違反  
**警告**：コードスメル、保守性の問題、軽微な規約違反  
**提案**：最適化、代替アプローチ、スタイルの好み

重大の明確化：
- `JdbcTemplate` / `NamedParameterJdbcTemplate` の注入・利用が Controller / Service / Security / Config に存在する場合は、レイヤー規約違反として**重大**で指摘する

---

## ファイルタイプ別の重点領域

**Controller（`*Controller.java`）**：
- HTTP 処理のみ
- ビジネスロジックが含まれていないか
- 適切な HTTP メソッドとステータスコード
- `@Valid` によるバリデーション
- 例外処理を Controller で行っていないか

**Service（`*Service.java`）**：
- ビジネスロジックの実装
- トランザクション管理（`@Transactional`）
- データ変換（DTO ↔ Entity）
- 外部 API 呼び出し
- 適切な例外のスロー
- スレッドセーフティ（Singleton かつ可変インスタンス変数がないか）
- `JdbcTemplate` / `NamedParameterJdbcTemplate` の直接利用がないか（DB アクセスは Mapper 経由のみ）

**Mapper（`*Mapper.java` と `*Mapper.xml`）**：
- データベースアクセスのみ
- SQL の品質（`SELECT *` 禁止、パラメータバインディング）
- ResultMap の定義
- インデックスの考慮

**DTO（`*Request.java`、`*Response.java`）**：
- バリデーションアノテーション
- デフォルト値の不使用
- 多言語対応メッセージ
- Lombok の活用

**Entity（`*Entity.java`）**：
- テーブル構造との対応
- フィールドの説明コメント
- Lombok の活用

**Config（`*Config.java`）**：
- セキュリティ設定（CORS、認証）
- Bean の定義
- プロパティの管理
- スレッドセーフティ（Singleton Bean に可変状態を持たせていないか）
- DB クエリ実装が混入していないか（`JdbcTemplate` / `NamedParameterJdbcTemplate` での直接クエリ禁止）

---

## 出力形式（タスク B）

常に以下を提供する：

1. レビューしたファイルのサマリー
2. 重要度別の問題数
3. ファイル:行参照付きの詳細な結果
4. 実行可能な推奨事項
5. 良い実践例に対する肯定的なフィードバック

フィードバックは建設的、具体的、実行可能なものにする。

## 参照ファイル

生成・レビュー中に必要に応じて読み込む。各観点の詳細は上記レビューチェックリストの各カテゴリ直下の参照を参照。

- **[naming-conventions.md](references/naming-conventions.md)**：バックエンドコードの完全な命名規則
- **[layer-architecture.md](references/layer-architecture.md)**：レイヤーアーキテクチャのルール
- **[dto-validation.md](references/dto-validation.md)**：DTO バリデーションのルール
- **[mybatis-sql.md](references/mybatis-sql.md)**：MyBatis SQL のルール
- **[security.md](references/security.md)**：セキュリティのルール
- **[spring-boot-best-practices.md](references/spring-boot-best-practices.md)**：Spring Boot ベストプラクティス
- **[logging.md](references/logging.md)**：ログ追跡用 ID（traceId）・ログ番号の形式と実装
- **[thread-safety.md](references/thread-safety.md)**：スレッドセーフティ（Singleton + 可変インスタンス変数のチェック）
- **[comment-checklist.md](references/comment-checklist.md)**：コメントとドキュメントの基準
- **[exception-handling.md](references/exception-handling.md)**：例外処理の統一ルール
