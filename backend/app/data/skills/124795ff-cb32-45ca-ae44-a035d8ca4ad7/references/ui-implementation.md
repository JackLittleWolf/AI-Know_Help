# UI 実装規約（開発者向け）

フロントエンド実装時に従う UI 周りの規約です。**見た目の定義は `index.css` に集約し、コンポーネントではクラス名のみ参照してください。** デザイン仕様はプロジェクトの `docs/rules/coding/frontend/UIDesign/UI_DESIGN_SPEC.md` を参照してください。

---

## 1. 方針

| 方針 | 説明 |
|------|------|
| **スタイル集約** | 見た目は `frontend/src/index.css` の `@layer components` に定義し、コンポーネントではクラス名だけを指定する。 |
| **セマンティック** | 役割が分かるクラス名（`card-meeting`、`title-page` など）を使い、長い Tailwind の羅列は避ける。必要なら index.css に新クラスを追加する。 |
| **定数利用** | 状態別の色・ボタン種別は `constants/colors.ts` の `STATUS_COLORS` / `PRIORITY_COLORS` / `BUTTON_VARIANTS` / `INPUT_COLORS` を参照する。 |

---

## 2. ファイルと責務

| ファイル | 責務 |
|----------|------|
| `frontend/src/index.css` | 共通 UI クラス（`@layer components`）。**スタイル変更はここに集約する。** |
| `frontend/tailwind.config.js` | テーマ拡張（色・フォント・シャドウ・アニメーション）。 |
| `frontend/src/constants/colors.ts` | 状態別クラス名（STATUS_COLORS、PRIORITY_COLORS、BUTTON_VARIANTS、INPUT_COLORS）。 |
| 各コンポーネント | 上記のクラス名を `className` で参照。インラインで長い Tailwind を書かず、必要なら index.css にクラスを追加する。 |

---

## 3. コンポーネント別クラス一覧

### 3.1 カード

| クラス | 用途 |
|--------|------|
| `card` | 基本カード |
| `card-dashed` | 破線ボーダーの補助カード |
| `card-hover` | ホバー時の変化（カードに付与） |
| `card-inner` | カード内くぼみ（空状態など） |
| `card-padded` | card + パディング |
| `card-link` | リンクカード |
| `card-meeting` | 会議カード（左アクセント線） |
| `card-meeting-inner` / `card-meeting-body` / `card-meeting-meta` | 会議カード内部 |
| `card-link-todo` | TODO 項目リンクカード |
| `sidebar-card` | サイドバー用カード |
| `card-login` | ログインフォーム用 |

### 3.2 ヘッダー・レイアウト

| クラス | 用途 |
|--------|------|
| `top-header` | トップページヘッダー |
| `top-header-actions` | ヘッダー内操作エリア |
| `top-header-user` | ログイン中ユーザー名 |
| `page-container` | ページ外枠 |
| `page-grid-main` | 2カラムの親（grid） |
| `page-grid-content` | メインエリア（lg:col-span-2） |
| `page-grid-aside` | サイドバー（lg:col-span-1） |
| `meeting-grid` | 会議カードグリッド（1列） |
| `meeting-grid-multi` | 2件以上時 2列（`meeting-grid` と併用） |

### 3.3 ボタン・フォーム

| クラス | 用途 |
|--------|------|
| `btn-primary` / `btn-primary-lg` | プライマリボタン |
| `btn-secondary` | セカンダリボタン |
| `btn-outline-blue` | 青枠ボタン |
| `input-base` / `input-base-sm` | テキスト入力 |
| `label-form` | ラベル |

disabled 等の複合が必要な場合は `BUTTON_VARIANTS`（constants/colors.ts）を参照。

### 3.4 タイポグラフィ・テキスト

| クラス | 用途 |
|--------|------|
| `title-page` | ページタイトル |
| `title-section` | セクションタイトル |
| `title-card` | カードタイトル |
| `subtitle` | サブタイトル・補足 |
| `text-body` | 本文 |
| `text-heading` | 見出し用テキスト |
| `text-muted` | 補足・弱いテキスト |

### 3.5 バッジ・アバター・TODO

| クラス | 用途 |
|--------|------|
| `badge-count` | 件数バッジ（○件） |
| `avatar-group` | アバター重ねラッパー |
| `avatar` / `avatar-more` | アバター / +N |
| `todo-list` | TODO リスト縦並び |
| `todo-item-badges` / `todo-item-title` / `todo-item-desc` / `todo-item-due` | TODO 1件内 |
| `sidebar-card-header` / `sidebar-card-footer` / `sidebar-card-footer-link` | サイドバーカード |
| `sidebar-loading` | サイドバー内ローディング |
| `meeting-location` | 会議の場所表示 |

ステータス・優先度バッジは `StatusBadge` / `PriorityBadge` と `STATUS_COLORS` / `PRIORITY_COLORS` を使用する。

### 3.6 フィードバック・オーバーレイ

| クラス | 用途 |
|--------|------|
| `spinner` / `spinner-sm` | ローディング |
| `modal-backdrop` / `modal-panel` | モーダル |
| `alert-error` / `alert-success` | エラー・成功メッセージ |
| `link-muted` | 補足リンク |
| `page-center` / `page-center-sm` | 中央配置 |
| `streaming-box` / `streaming-box-header` / `streaming-box-body` | AI ストリーミング |

---

## 4. 定数（constants/colors.ts）

- **STATUS_COLORS**: 未着手 / 進行中 / 完了 のバッジ用 `bg`・`text` クラス。
- **PRIORITY_COLORS**: 高 / 中 / 低 のバッジ用 `bg`・`text` クラス。
- **BUTTON_VARIANTS**: primary / secondary / success / danger / outline の `base`・`text`・`disabled`。
- **INPUT_COLORS**: default / error / success のフォーカス・枠用クラス。

新規状態を増やす場合はここに追加し、既存パターンに合わせる。

---

## 5. レスポンシブ

- ブレークポイント: `sm`（640px）、`lg`（1024px）を基本とする。
- 会議カード: 1件は `meeting-grid` のみ、2件以上は `meeting-grid meeting-grid-multi` で 2列。
- セクションには `aria-label` を付与（例: 「会議一覧」「マイTODO」）。

---

## 6. アクセシビリティ（実装）

- ボタンは submit でない場合 `type="button"` を明示する。
- アイコンのみの操作には `title` または `aria-label` を付与する。
- フォーカスは `focus:ring-2 focus:ring-morandi-blue-500` で視認可能に（共通クラス内で定義済みの場合はそのまま利用）。

---

## 7. 要素の id（命名規則）

E2E テストやアクセシビリティで安定して参照するため、**主要な操作・ランドマーク要素には id を付与する**。id は文書内で一意とする。

| 項目 | 規則 |
|------|------|
| **形式** | **kebab-case**（小文字＋ハイフン）。例：`login-username`、`confirm-dialog-title`。 |
| **一意性** | 文書内で一意。リスト・カードなど繰り返し要素は「プレフィックス-役割-業務主キー」で区別する（例：`meeting-card-${meeting.id}`）。 |
| **プレフィックス** | ページまたはコンポーネント名をプレフィックスにし、他画面・共通コンポーネントとの衝突を防ぐ。 |

**命名パターン**

- **単一要素（ページ内で 1 つ）**：`{ページまたはコンポーネント}-{要素の役割}`  
  例：`login-username`、`login-submit`、`meeting-list-refresh`、`meeting-detail-edit-btn`、`confirm-dialog-title`。
- **繰り返し要素（リスト・カード等）**：`{ページまたはコンポーネント}-{要素の役割}-{唯一キー}`  
  例：`meeting-card-${meeting.id}`、`todo-item-${todo.id}`。
- **共通コンポーネント**：コンポーネント名をプレフィックスにする。  
  例：`confirm-dialog-cancel`、`confirm-dialog-confirm`。

**id を付与する範囲**

- **必須**：フォームコントロール（input / select / textarea）、送信・主要操作ボタン、主要ナビゲーションリンク、ダイアログ／モーダルとそのタイトル・主要ボタン、リスト／カードなどクリックまたは識別するブロック（リスト項目は上記「プレフィックス-役割-唯一キー」）。
- **推奨**：ページ主タイトル（h1）、主要セクション見出し（h2/h3）、セクションランドマーク（`aria-label` と併用）。
- **任意**：装飾のみの wrapper・レイアウト用 div は必須としない。

---

## 8. 新規画面追加時のチェックリスト

- [ ] ページ外枠に `page-container` を使用したか
- [ ] 見出しに `title-page` / `title-section` を使用したか
- [ ] カードは `card` 系の共通クラスを使ったか
- [ ] ボタンは `btn-primary` / `btn-secondary` または BUTTON_VARIANTS を使ったか
- [ ] 長い className が続く場合は index.css にクラスを追加したか
- [ ] 色はモランディパレット＋状態色（constants/colors.ts）に統一したか
- [ ] レスポンシブ（sm / lg）を考慮したか
- [ ] 主要なフォーム・ボタン・リンク・モーダル・リスト項目に id を付与し、命名規則（kebab-case・プレフィックス）に従っているか
