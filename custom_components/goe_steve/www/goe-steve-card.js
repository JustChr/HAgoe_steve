/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Nt=Object.defineProperty;var kt=Object.getOwnPropertyDescriptor;var v=(r,t,e,s)=>{for(var i=s>1?void 0:s?kt(t,e):t,n=r.length-1,o;n>=0;n--)(o=r[n])&&(i=(s?o(t,e,i):o(i))||i);return s&&i&&Nt(t,e,i),i};var B=globalThis,I=B.ShadowRoot&&(B.ShadyCSS===void 0||B.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,G=Symbol(),ut=new WeakMap,N=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==G)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(I&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=ut.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&ut.set(e,t))}return t}toString(){return this.cssText}},gt=r=>new N(typeof r=="string"?r:r+"",void 0,G),k=(r,...t)=>{let e=r.length===1?r[0]:t.reduce((s,i,n)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+r[n+1],r[0]);return new N(e,r,G)},mt=(r,t)=>{if(I)r.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=B.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,r.appendChild(s)}},tt=I?r=>r:r=>r instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return gt(e)})(r):r;var{is:Ht,defineProperty:Tt,getOwnPropertyDescriptor:Ut,getOwnPropertyNames:Lt,getOwnPropertySymbols:jt,getPrototypeOf:zt}=Object,F=globalThis,ft=F.trustedTypes,Dt=ft?ft.emptyScript:"",qt=F.reactiveElementPolyfillSupport,H=(r,t)=>r,T={toAttribute(r,t){switch(t){case Boolean:r=r?Dt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,t){let e=r;switch(t){case Boolean:e=r!==null;break;case Number:e=r===null?null:Number(r);break;case Object:case Array:try{e=JSON.parse(r)}catch{e=null}}return e}},W=(r,t)=>!Ht(r,t),_t={attribute:!0,type:String,converter:T,reflect:!1,useDefault:!1,hasChanged:W};Symbol.metadata??=Symbol("metadata"),F.litPropertyMetadata??=new WeakMap;var y=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=_t){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Tt(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:n}=Ut(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let c=i?.call(this);n?.call(this,o),this.requestUpdate(t,c,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??_t}static _$Ei(){if(this.hasOwnProperty(H("elementProperties")))return;let t=zt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(H("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(H("properties"))){let e=this.properties,s=[...Lt(e),...jt(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(tt(i))}else t!==void 0&&e.push(tt(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return mt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let n=(s.converter?.toAttribute!==void 0?s.converter:T).toAttribute(e,s.type);this._$Em=t,n==null?this.removeAttribute(i):this.setAttribute(i,n),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let n=s.getPropertyOptions(i),o=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:T;this._$Em=i;let c=o.fromAttribute(e,n.type);this[i]=c??this._$Ej?.get(i)??c,this._$Em=null}}requestUpdate(t,e,s,i=!1,n){if(t!==void 0){let o=this.constructor;if(i===!1&&(n=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??W)(n,e)||s.useDefault&&s.reflect&&n===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:n},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),n!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,n]of this._$Ep)this[i]=n;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,n]of s){let{wrapped:o}=n,c=this[i];o!==!0||this._$AL.has(i)||c===void 0||this.C(i,void 0,n,c)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};y.elementStyles=[],y.shadowRootOptions={mode:"open"},y[H("elementProperties")]=new Map,y[H("finalized")]=new Map,qt?.({ReactiveElement:y}),(F.reactiveElementVersions??=[]).push("2.1.2");var at=globalThis,yt=r=>r,V=at.trustedTypes,vt=V?V.createPolicy("lit-html",{createHTML:r=>r}):void 0,Et="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,St="?"+$,Bt=`<${St}>`,x=document,L=()=>x.createComment(""),j=r=>r===null||typeof r!="object"&&typeof r!="function",ct=Array.isArray,It=r=>ct(r)||typeof r?.[Symbol.iterator]=="function",et=`[ 	
\f\r]`,U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,$t=/-->/g,bt=/>/g,b=RegExp(`>|${et}(?:([^\\s"'>=/]+)(${et}*=${et}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),wt=/'/g,xt=/"/g,Ct=/^(?:script|style|textarea|title)$/i,lt=r=>(t,...e)=>({_$litType$:r,strings:t,values:e}),p=lt(1),ht=lt(2),te=lt(3),A=Symbol.for("lit-noChange"),l=Symbol.for("lit-nothing"),At=new WeakMap,w=x.createTreeWalker(x,129);function Rt(r,t){if(!ct(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return vt!==void 0?vt.createHTML(t):t}var Ft=(r,t)=>{let e=r.length-1,s=[],i,n=t===2?"<svg>":t===3?"<math>":"",o=U;for(let c=0;c<e;c++){let a=r[c],d,u,h=-1,g=0;for(;g<a.length&&(o.lastIndex=g,u=o.exec(a),u!==null);)g=o.lastIndex,o===U?u[1]==="!--"?o=$t:u[1]!==void 0?o=bt:u[2]!==void 0?(Ct.test(u[2])&&(i=RegExp("</"+u[2],"g")),o=b):u[3]!==void 0&&(o=b):o===b?u[0]===">"?(o=i??U,h=-1):u[1]===void 0?h=-2:(h=o.lastIndex-u[2].length,d=u[1],o=u[3]===void 0?b:u[3]==='"'?xt:wt):o===xt||o===wt?o=b:o===$t||o===bt?o=U:(o=b,i=void 0);let m=o===b&&r[c+1].startsWith("/>")?" ":"";n+=o===U?a+Bt:h>=0?(s.push(d),a.slice(0,h)+Et+a.slice(h)+$+m):a+$+(h===-2?c:m)}return[Rt(r,n+(r[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},z=class r{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let n=0,o=0,c=t.length-1,a=this.parts,[d,u]=Ft(t,e);if(this.el=r.createElement(d,s),w.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=w.nextNode())!==null&&a.length<c;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(Et)){let g=u[o++],m=i.getAttribute(h).split($),_=/([.?@])?(.*)/.exec(g);a.push({type:1,index:n,name:_[2],strings:m,ctor:_[1]==="."?it:_[1]==="?"?nt:_[1]==="@"?rt:R}),i.removeAttribute(h)}else h.startsWith($)&&(a.push({type:6,index:n}),i.removeAttribute(h));if(Ct.test(i.tagName)){let h=i.textContent.split($),g=h.length-1;if(g>0){i.textContent=V?V.emptyScript:"";for(let m=0;m<g;m++)i.append(h[m],L()),w.nextNode(),a.push({type:2,index:++n});i.append(h[g],L())}}}else if(i.nodeType===8)if(i.data===St)a.push({type:2,index:n});else{let h=-1;for(;(h=i.data.indexOf($,h+1))!==-1;)a.push({type:7,index:n}),h+=$.length-1}n++}}static createElement(t,e){let s=x.createElement("template");return s.innerHTML=t,s}};function C(r,t,e=r,s){if(t===A)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,n=j(t)?void 0:t._$litDirective$;return i?.constructor!==n&&(i?._$AO?.(!1),n===void 0?i=void 0:(i=new n(r),i._$AT(r,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=C(r,i._$AS(r,t.values),i,s)),t}var st=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??x).importNode(e,!0);w.currentNode=i;let n=w.nextNode(),o=0,c=0,a=s[0];for(;a!==void 0;){if(o===a.index){let d;a.type===2?d=new D(n,n.nextSibling,this,t):a.type===1?d=new a.ctor(n,a.name,a.strings,this,t):a.type===6&&(d=new ot(n,this,t)),this._$AV.push(d),a=s[++c]}o!==a?.index&&(n=w.nextNode(),o++)}return w.currentNode=x,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},D=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=l,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=C(this,t,e),j(t)?t===l||t==null||t===""?(this._$AH!==l&&this._$AR(),this._$AH=l):t!==this._$AH&&t!==A&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):It(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==l&&j(this._$AH)?this._$AA.nextSibling.data=t:this.T(x.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=z.createElement(Rt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let n=new st(i,this),o=n.u(this.options);n.p(e),this.T(o),this._$AH=n}}_$AC(t){let e=At.get(t.strings);return e===void 0&&At.set(t.strings,e=new z(t)),e}k(t){ct(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let n of t)i===e.length?e.push(s=new r(this.O(L()),this.O(L()),this,this.options)):s=e[i],s._$AI(n),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=yt(t).nextSibling;yt(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},R=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,n){this.type=1,this._$AH=l,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=n,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=l}_$AI(t,e=this,s,i){let n=this.strings,o=!1;if(n===void 0)t=C(this,t,e,0),o=!j(t)||t!==this._$AH&&t!==A,o&&(this._$AH=t);else{let c=t,a,d;for(t=n[0],a=0;a<n.length-1;a++)d=C(this,c[s+a],e,a),d===A&&(d=this._$AH[a]),o||=!j(d)||d!==this._$AH[a],d===l?t=l:t!==l&&(t+=(d??"")+n[a+1]),this._$AH[a]=d}o&&!i&&this.j(t)}j(t){t===l?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},it=class extends R{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===l?void 0:t}},nt=class extends R{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==l)}},rt=class extends R{constructor(t,e,s,i,n){super(t,e,s,i,n),this.type=5}_$AI(t,e=this){if((t=C(this,t,e,0)??l)===A)return;let s=this._$AH,i=t===l&&s!==l||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,n=t!==l&&(s===l||i);i&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},ot=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){C(this,t)}};var Wt=at.litHtmlPolyfillSupport;Wt?.(z,D),(at.litHtmlVersions??=[]).push("3.3.3");var Ot=(r,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let n=e?.renderBefore??null;s._$litPart$=i=new D(t.insertBefore(L(),n),n,void 0,e??{})}return i._$AI(r),i};var dt=globalThis,f=class extends y{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Ot(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return A}};f._$litElement$=!0,f.finalized=!0,dt.litElementHydrateSupport?.({LitElement:f});var Vt=dt.litElementPolyfillSupport;Vt?.({LitElement:f});(dt.litElementVersions??=[]).push("4.2.2");var K=r=>(t,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(r,t)}):customElements.define(r,t)};var Kt={attribute:!0,type:String,converter:T,reflect:!1,hasChanged:W},Jt=(r=Kt,t,e)=>{let{kind:s,metadata:i}=e,n=globalThis.litPropertyMetadata.get(i);if(n===void 0&&globalThis.litPropertyMetadata.set(i,n=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),n.set(e.name,r),s==="accessor"){let{name:o}=e;return{set(c){let a=t.get.call(this);t.set.call(this,c),this.requestUpdate(o,a,r,!0,c)},init(c){return c!==void 0&&this.C(o,void 0,r,c),c}}}if(s==="setter"){let{name:o}=e;return function(c){let a=this[o];t.call(this,c),this.requestUpdate(o,a,r,!0,c)}}throw Error("Unsupported decorator location: "+s)};function O(r){return(t,e)=>typeof e=="object"?Jt(r,t,e):((s,i,n)=>{let o=i.hasOwnProperty(n);return i.constructor.createProperty(n,s),o?Object.getOwnPropertyDescriptor(i,n):void 0})(r,t,e)}function J(r){return O({...r,state:!0,attribute:!1})}var P="goe_steve";function pt(r){let t=new Map;for(let e of Object.values(r.entities))if(!(e.platform!==P||!e.device_id)&&!t.has(e.device_id)){let s=r.devices[e.device_id];t.set(e.device_id,s?.name_by_user||s?.name||e.device_id)}return[...t.entries()].map(([e,s])=>({id:e,name:s}))}function Pt(r,t){let e={tag_energy:[]};if(!t){let n=pt(r);n.length===1&&(t=n[0].id)}if(e.deviceId=t,!t)return e;let s=Object.values(r.entities).filter(n=>n.platform===P&&n.device_id===t),i=n=>{let o=s.find(a=>a.translation_key===n);return o?o.entity_id:s.find(a=>{let d=a.entity_id.split(".")[1]??"";return d===n||d.endsWith(`_${n}`)})?.entity_id};return e.status=i("status"),e.power_flow=i("power_flow"),e.surplus=i("surplus_for_car"),e.target_current=i("target_current"),e.controlling=i("controlling"),e.charging_mode=i("charging_mode"),e.battery_policy=i("battery_policy"),e.smart_control=i("smart_control"),e.auto_phase=i("auto_phase"),e.active_transaction=i("active_transaction"),e.last_session_energy=i("last_session_energy"),e.tag_energy=s.filter(n=>n.translation_key==="tag_energy"||n.entity_id.split(".")[1]?.includes("_tag_energy_")).map(n=>n.entity_id).sort(),e}var E=class extends f{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:P}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return"Smart Charging device (optional \u2014 auto-detected)";case"title":return"Title (optional)";case"show_flow":return"Show energy flow";case"show_controls":return"Show controls";case"show_sessions":return"Show sessions & RFID";default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};E.styles=k`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,v([O({attribute:!1})],E.prototype,"hass",2),v([J()],E.prototype,"_config",2),E=v([K("goe-steve-card-editor")],E);var q=r=>{if(r==null||Number.isNaN(r))return"\u2014";let t=Math.abs(r);return t>=1e3?`${(r/1e3).toFixed(t>=1e4?0:1)} kW`:`${Math.round(r)} W`},S=class extends f{static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:pt(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,...t}}getCardSize(){return 8}get _entities(){return this.hass?Pt(this.hass,this._config?.device):null}render(){if(!this.hass||!this._config)return l;let t=this._entities;if(!t||!t.deviceId)return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>No <b>go-e + SteVe Smart Charging</b> device found. Set one up first, then add this card.</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??"Smart Charging";return p`<ha-card>
      ${this._renderHeader(t,e)}
      <div class="content">
        ${this._config.show_flow?this._renderFlow(t):l}
        ${this._config.show_controls?this._renderControls(t):l}
        ${this._config.show_sessions?this._renderSessions(t):l}
      </div>
    </ha-card>`}_renderHeader(t,e){let s=this._stateObj(t.status),i=s?.state&&s.state!=="unknown"?s.state:"\u2014",n=this._isOn(t.controlling),o=this._displayState(t.charging_mode),c=this._displayState(t.battery_policy);return p`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${n?"active":""}" icon="mdi:brain"></ha-icon>
        <span class="title">${e}</span>
      </div>
      <div class="reason">${i}</div>
      <div class="chips">
        ${o?p`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${o}</span>`:l}
        ${c?p`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${c}</span>`:l}
      </div>
    </div>`}_renderFlow(t){let e=this._stateObj(t.power_flow),s=e?.attributes??{},i=Number(s.pv_w??NaN),n=Number(s.grid_w??NaN),o=s.battery_w===null||s.battery_w===void 0?null:Number(s.battery_w),c=Number(s.car_w??(e?e.state:NaN)),a=Number(s.house_w??NaN),d=s.battery_soc,u=s.car_connected,h=50,g=(_,M,Z,Q,X,Mt="")=>ht`
      <g class="node" transform="translate(${_},${M})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${Z}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${X}</text>
        <text class="node-lbl" y="42">${Q}${Mt}</text>
      </g>`,m=(_,M,Z,Q)=>{let X=M?Math.max(.6,3-Math.min(Q,9e3)/3e3):0;return ht`
        <path class="edge" d="${_}"></path>
        <path
          class="edge-flow ${M?"active":""} ${Z?"rev":""}"
          d="${_}"
          style="${M?`animation-duration:${X}s`:""}"
        ></path>`};return p`<div class="flow">
      <svg viewBox="0 0 320 320" preserveAspectRatio="xMidYMid meet">
        ${m("M160,66 L160,134",i>h,!1,i)}
        ${m("M76,160 L134,160",Number.isNaN(n)?!1:Math.abs(n)>h,n<0,Math.abs(n))}
        ${o!==null?m("M244,160 L186,160",Math.abs(o)>h,o>0,Math.abs(o)):l}
        ${m("M160,186 L160,244",c>h,!1,c)}

        ${g(160,40,"mdi:solar-power","Solar",q(i))}
        ${g(40,160,"mdi:transmission-tower",n<0?"Export":"Grid",q(Math.abs(n)))}
        ${o!==null?g(280,160,"mdi:home-battery","Battery",q(Math.abs(o)),d!=null?` ${Math.round(Number(d))}%`:""):l}
        ${g(160,160,"mdi:home","Home",q(a))}
        ${g(160,280,u===!1?"mdi:car-off":"mdi:car-electric",u===!1?"No car":"Car",q(c))}
      </svg>
    </div>`}_renderControls(t){let e=this._stateObj(t.charging_mode),s=this._stateObj(t.battery_policy),i=this._stateObj(t.smart_control);return p`<div class="controls">
      ${e?p`<div class="control">
            <span class="ctl-label">Mode</span>
            ${this._renderSelect(e)}
          </div>`:l}
      ${s?p`<div class="control">
            <span class="ctl-label">Battery</span>
            ${this._renderSelect(s)}
          </div>`:l}
      ${i?p`<div class="control">
            <span class="ctl-label">Smart control</span>
            <ha-switch
              .checked=${this._isOn(t.smart_control)}
              @change=${n=>this._toggle(t.smart_control,n)}
            ></ha-switch>
          </div>`:l}
    </div>`}_renderSelect(t){let e=t.attributes.options??[];return p`<ha-select
      naturalMenuWidth
      .value=${t.state}
      @selected=${s=>this._selectOption(t,s.target.value)}
      @closed=${s=>s.stopPropagation()}
    >
      ${e.map(s=>p`<mwc-list-item .value=${s}>${this._localizeOption(t,s)}</mwc-list-item>`)}
    </ha-select>`}_renderSessions(t){let e=this._stateObj(t.active_transaction),s=this._stateObj(t.last_session_energy),i=t.tag_energy.map(n=>this._stateObj(n)).filter(n=>!!n);return!e&&!s&&i.length===0?l:p`<div class="sessions">
      ${e?p`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${e.state==="idle"?"No active session":`Charging: ${e.state}`}</span>
          </div>`:l}
      ${s&&s.state&&s.state!=="unknown"?p`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>Last session: ${this._fmtState(s)}</span>
          </div>`:l}
      ${i.length?p`<div class="tags">
            ${i.map(n=>p`<div class="tag">
                <span class="tag-id">${n.attributes.id_tag??"tag"}</span>
                <span class="tag-kwh ${n.attributes.blocked?"blocked":""}">
                  ${this._fmtState(n)}${n.attributes.blocked?" \xB7 blocked":""}
                </span>
              </div>`)}
          </div>`:l}
    </div>`}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_displayState(t){let e=this._stateObj(t);return e?this._fmtState(e):null}_fmtState(t){return this.hass.formatEntityState?this.hass.formatEntityState(t):t.state}_localizeOption(t,e){let i=this.hass.entities[t.entity_id]?.translation_key;if(i){let n=this.hass.localize(`component.${P}.entity.select.${i}.state.${e}`);if(n)return n}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let s=e.target.checked;this.hass.callService("switch",s?"turn_on":"turn_off",{entity_id:t})}};S.styles=k`
    ha-card {
      overflow: hidden;
    }
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 24px;
      color: var(--secondary-text-color);
      text-align: center;
    }
    .empty ha-icon {
      --mdc-icon-size: 40px;
      color: var(--disabled-text-color);
    }
    .header {
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .brain {
      color: var(--disabled-text-color);
      transition: color 0.3s ease;
    }
    .brain.active {
      color: var(--primary-color);
    }
    .reason {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.95rem;
      min-height: 1.2em;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      font-size: 0.8rem;
      color: var(--primary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 15px;
      color: var(--primary-color);
    }
    .content {
      padding: 0 8px 8px;
    }

    /* Flow diagram */
    .flow svg {
      width: 100%;
      height: auto;
      max-height: 320px;
    }
    .node circle {
      fill: var(--card-background-color);
      stroke: var(--divider-color);
      stroke-width: 1.5;
    }
    .node ha-icon {
      --mdc-icon-size: 22px;
      color: var(--primary-color);
    }
    .node-val {
      text-anchor: middle;
      font-size: 11px;
      font-weight: 600;
      fill: var(--primary-text-color);
    }
    .node-lbl {
      text-anchor: middle;
      font-size: 10px;
      fill: var(--secondary-text-color);
    }
    .edge {
      fill: none;
      stroke: var(--divider-color);
      stroke-width: 2;
    }
    .edge-flow {
      fill: none;
      stroke: var(--primary-color);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 4 10;
      opacity: 0;
    }
    .edge-flow.active {
      opacity: 0.9;
      animation-name: dash;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
    }
    .edge-flow.active.rev {
      animation-name: dash-rev;
    }
    @keyframes dash {
      to {
        stroke-dashoffset: -14;
      }
    }
    @keyframes dash-rev {
      to {
        stroke-dashoffset: 14;
      }
    }

    /* Controls */
    .controls {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 4px 8px 8px;
    }
    .control {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctl-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
      white-space: nowrap;
    }
    ha-select {
      min-width: 180px;
    }

    /* Sessions */
    .sessions {
      border-top: 1px solid var(--divider-color);
      margin: 4px 8px 0;
      padding-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .session-row ha-icon {
      --mdc-icon-size: 18px;
      color: var(--secondary-text-color);
    }
    .tags {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 2px;
    }
    .tag {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      padding: 2px 0;
    }
    .tag-id {
      color: var(--secondary-text-color);
    }
    .tag-kwh {
      font-weight: 600;
    }
    .tag-kwh.blocked {
      color: var(--error-color, #db4437);
      font-weight: 500;
    }
  `,v([O({attribute:!1})],S.prototype,"hass",2),v([J()],S.prototype,"_config",2),S=v([K("goe-steve-card")],S);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{S as GoeSteveCard};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/custom-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/property.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/state.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/event-options.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/base.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-all.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-async.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
